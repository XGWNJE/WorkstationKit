@echo off
rem ============================================================================
rem  Windows 7 无人值守置备脚本（实测可用）
rem
rem  放在应答光盘的根目录，由 Autounattend.xml 的 FirstLogonCommands 调起。
rem
rem  做三件事，且跨重启自续：
rem    phase1  ：装 KB4490628 → KB4474419（SHA-2 支持），然后重启
rem    phase2  ：装 VMware Tools
rem    verify  ：输出核验信息
rem
rem  设计约束：
rem    1. 状态机直接检查补丁与 VMware Tools 的真实安装状态。
rem    2. 装一个"登录自续钩子"，重启后自动继续。
rem    3. 日志写文件，便于事后排查（客机没装 Tools 时可从宿主机读 VMDK 取出）。
rem ============================================================================

setlocal enabledelayedexpansion
set LOG=C:\w7payload.log
set SRC=%~dp0
set PHASE=%~1
set TOOLSDIR=%ProgramFiles%\VMware\VMware Tools
if "%PHASE%"=="" set PHASE=auto

echo. >> "%LOG%"
echo ==== start phase=%PHASE% src=%SRC% at %DATE% %TIME% ==== >> "%LOG%"
ver >> "%LOG%" 2>&1

rem --- 登录自续钩子：重启后由登录事件再次调起本脚本 ---
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v w7payload >nul 2>&1
if not errorlevel 1 goto hookdone
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v w7payload /t REG_SZ /d "cmd.exe /c for %%i in (D: E: F: G: H: I: J:) do @if exist %%i\w7payload.cmd call %%i\w7payload.cmd auto" /f >> "%LOG%" 2>&1
echo hook reg rc=!ERRORLEVEL! >> "%LOG%"
:hookdone

if /I "%PHASE%"=="phase1" goto phase1
if /I "%PHASE%"=="phase2" goto phase2
if /I "%PHASE%"=="verify" goto verify

rem --- auto：只按真实状态决定下一步 ---
wmic qfe get HotFixID 2>nul | findstr /I "KB4474419" >nul 2>&1
if errorlevel 1 (
  echo auto: KB4474419 absent -^> phase1 >> "%LOG%"
  goto phase1
)
if not exist "%TOOLSDIR%\vmtoolsd.exe" (
  echo auto: VMware Tools absent -^> phase2 >> "%LOG%"
  goto phase2
)
echo auto: nothing pending >> "%LOG%"
goto verify

:phase1
echo --- phase1: uac off + prerequisite updates --- >> "%LOG%"
wmic logicaldisk get caption,volumename,size >> "%LOG%" 2>&1

rem 关闭 UAC：让置备命令在无人值守下也能提权执行。
rem 这是可逆的（把 1 写回去并重启即恢复），如不需要可删除本段。
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableLUA /t REG_DWORD /d 0 /f >> "%LOG%" 2>&1
echo EnableLUA=0 rc=!ERRORLEVEL! >> "%LOG%"

rem 顺序不能颠倒：KB4474419（SHA-2 支持）依赖 KB4490628（服务堆栈）
if not exist "%SRC%kb4490628-x64.msu" goto nokb4490628
echo installing KB4490628 >> "%LOG%"
wusa.exe "%SRC%kb4490628-x64.msu" /quiet /norestart >> "%LOG%" 2>&1
echo KB4490628 rc=!ERRORLEVEL! >> "%LOG%"
goto kb4474419
:nokb4490628
echo MISSING kb4490628-x64.msu >> "%LOG%"

:kb4474419
if not exist "%SRC%kb4474419-v3-x64.msu" goto nokb4474419
echo installing KB4474419 >> "%LOG%"
wusa.exe "%SRC%kb4474419-v3-x64.msu" /quiet /norestart >> "%LOG%" 2>&1
echo KB4474419 rc=!ERRORLEVEL! >> "%LOG%"
goto kbend
:nokb4474419
echo MISSING kb4474419-v3-x64.msu >> "%LOG%"

:kbend
echo phase1 done, rebooting >> "%LOG%"
shutdown /r /t 15 /f >> "%LOG%" 2>&1
echo shutdown rc=!ERRORLEVEL! >> "%LOG%"
if not errorlevel 1 goto end
echo shutdown failed, trying wmic >> "%LOG%"
wmic os where primary='TRUE' call reboot >> "%LOG%" 2>&1
echo wmic reboot rc=!ERRORLEVEL! >> "%LOG%"
goto end

:phase2
echo --- phase2: install vmware tools --- >> "%LOG%"
rem 用 VMwareToolsUpgrader.exe 作为识别标志：安装光盘根目录也有 setup.exe，不能只看文件名
set TOOLSCD=
for %%i in (D: E: F: G: H: I: J:) do @if exist "%%i\VMwareToolsUpgrader.exe" set TOOLSCD=%%i
echo toolscd=!TOOLSCD! >> "%LOG%"
if not defined TOOLSCD goto notools

echo launching tools setup >> "%LOG%"
start /wait "" "!TOOLSCD!\setup.exe" /s /v"/qn REBOOT=R"
echo tools setup returned rc=!ERRORLEVEL! >> "%LOG%"

rem 不信任启动器的退出码，轮询 Tools 服务程序是否真的出现
set /a WAITN=0
:waittools
if exist "%TOOLSDIR%\vmtoolsd.exe" goto toolsok
set /a WAITN+=1
if %WAITN% GEQ 60 goto toolstimeout
ping -n 6 127.0.0.1 >nul 2>&1
goto waittools

:toolsok
echo tools installed: vmtoolsd.exe present >> "%LOG%"
goto verify

:toolstimeout
echo ERROR: tools did not appear within 5 minutes >> "%LOG%"
goto verify

:notools
echo ERROR: VMware Tools CD not found >> "%LOG%"
goto end

:verify
echo --- verify --- >> "%LOG%"
wmic qfe get HotFixID,InstalledOn >> "%LOG%" 2>&1
sc query VMTools >> "%LOG%" 2>&1
reg query "HKLM\SOFTWARE\VMware, Inc.\VMware Tools" /v ProductVersion >> "%LOG%" 2>&1
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableLUA >> "%LOG%" 2>&1
if exist "%TOOLSDIR%\vmtoolsd.exe" echo vmtoolsd.exe present >> "%LOG%"
if not exist "%TOOLSDIR%\vmtoolsd.exe" echo vmtoolsd.exe absent >> "%LOG%"

rem --- 最终状态：User 无密码，并保持本地自动登录 ---
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v w7payload /f >> "%LOG%" 2>&1
net user User "" >> "%LOG%" 2>&1
echo clear User password rc=!ERRORLEVEL! >> "%LOG%"
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultUserName /t REG_SZ /d User /f >> "%LOG%" 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultPassword /t REG_SZ /d "" /f >> "%LOG%" 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v AutoAdminLogon /t REG_SZ /d 1 /f >> "%LOG%" 2>&1
reg delete "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v AutoLogonCount /f >> "%LOG%" 2>&1
echo final passwordless autologon configured >> "%LOG%"
shutdown /r /t 15 /f >> "%LOG%" 2>&1
goto end

:end
echo ==== end phase=%PHASE% at %DATE% %TIME% ==== >> "%LOG%"
endlocal

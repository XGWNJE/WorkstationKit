# Windows 7 无人值守安装（VMware Workstation）

在一台 Windows 11 宿主机上，用 VMware Workstation 把 Windows 7 旗舰版 SP1 x64 装成虚拟机，**全程无需人工干预**，并自动装完前置补丁与 VMware Tools。

本文给出一条经过实机验证、可重复执行的完整流程：全新建盘、无人值守安装、补齐 SHA-2 支持、安装 VMware Tools，最后切换为无密码自动登录。

---

## 适用前提

- 宿主机：Windows 11，已装 VMware Workstation 26H1（其他版本同理）
- 安装镜像：`cn_windows_7_ultimate_with_sp1_x64_dvd_u_677408.iso`（微软 MSDN 原版，SHA1 `2ce0b2db34d76ed3f697ce148cb7594432405e23`）
- 宿主机虚拟化未被 Hyper-V 占用（本项目实测为 `HypervisorPresent=False`，VMware 走原生 VMM）

> 各项的**具体下载入口与校验值**见 [downloads.md](downloads.md)。安装包务必先验签名与哈希，镜像务必先比对 SHA1。

---

## 步骤 1：核验安装包

```powershell
# 安装包真实性：签名 + 版本
$p = '<安装包路径>.exe'
$s = Get-AuthenticodeSignature -LiteralPath $p
$s.Status                      # 期望 Valid
$s.SignerCertificate.Subject   # 期望 CN=Broadcom Inc
(Get-Item $p).VersionInfo.FileVersion
```

安装前建议建系统还原点（本机实测 30 秒内完成）：

```powershell
Checkpoint-Computer -Description 'Before Workstation install' -RestorePointModify MODIFY_SETTINGS
```

## 步骤 2：创建虚拟机

用 Workstation 自带的 `vmcli.exe` 建机，避免手工拼 vmx：

```bat
vmcli.exe VM Create -n "Windows 7 Ultimate x64" -d "<虚拟机目录>" -c windows7-64
```

它默认给的是 60 GB 磁盘与 512 MB 内存，需要自行纠正。`reference.vmx` 是实测可用的完整配置，要点：

| 配置项 | 值 | 为什么 |
|---|---|---|
| `firmware` | `bios` | Win7 标准安装走 BIOS/MBR；UEFI 需要特殊处理 |
| `sata0:0` | 30 GB 精简磁盘 | **Win7 x64 没有内置 NVMe 驱动**，必须用 SATA |
| `ethernet0.virtualDev` | `e1000` | Win7 自带 e1000 驱动；`vmxnet3` 要先装 Tools 才能用 |
| `usb_xhci.present` | `FALSE` | Win7 没有 USB3 驱动，保留 USB2.0 |
| `sata0:1` / `sata0:2` | 安装镜像 + 应答光盘 | 两张光驱 |
| `cpuid.coresPerSocket` | 与 `numvcpus` 相同 | 呈现为单插槽多核，兼容性最好 |

磁盘必须重建到目标容量（`vmcli VM Create` 的默认容量不可直接改）：

```bat
vmware-vdiskmanager.exe -c -s 30GB -a lsilogic -t 0 "<磁盘路径>.vmdk"
```

## 步骤 3：制作应答光盘

关键机制：**Windows 安装程序会扫描所有可移动介质的根目录寻找 `Autounattend.xml`**。所以不必改动原版镜像（改动会破坏哈希），只需**另建一张小光盘**：

```powershell
.\win7-unattend\New-UnattendIso.ps1 `
  -OutputIso '<虚拟机目录>\unattend.iso' `
  -Kb4490628 '<下载目录>\windows6.1-kb4490628-x64_....msu' `
  -Kb4474419 '<下载目录>\windows6.1-kb4474419-v3-x64_....msu'
```

构建脚本会完成四项检查和转换：校验两枚补丁的 SHA-1、生成随机安装临时密码、强制 `w7payload.cmd` 使用 CRLF、调用 Workstation 自带的 `mkisofs.exe` 生成 ISO。临时密码不会输出；置备完成后会从账户和自动登录配置中清除。

应答文件要点：

- `/IMAGE/INDEX` 取 **4**（该镜像内 1=家庭普通版 2=家庭高级版 3=专业版 4=旗舰版，可用 `dism /Get-WimInfo /WimFile:<盘>:\sources\install.wim` 核对）
- 单分区 + `WillWipeDisk`
- **跳过产品密钥**：`<ProductKey><Key></Key><WillShowUI>Never</WillShowUI></ProductKey>`
- 账户用 `UserAccounts/LocalAccounts` 建本地管理员；安装阶段 `AutoLogon` 使用相同的临时密码
- 不写 `AdministratorPassword`，该项不属于 Win7 的 oobeSystem 设置
- 批处理文件必须为 CRLF；始终通过 `New-UnattendIso.ps1` 构建应答光盘

## 步骤 4：启动安装

```bat
vmrun.exe -T ws start "<vmx路径>" nogui
```

无头模式启动，不会抢占宿主桌面焦点。安装期间可用 Workstation 自带的截屏核对进度：

```bat
vmcli.exe "<vmx路径>" MKS captureScreenshot "<输出>.png"
```

---

## 可重复安装约束

每次执行都从新建虚拟磁盘开始，并在置备完成后断开安装光盘、应答光盘和 Tools 光盘。这样安装输入、磁盘状态和启动顺序保持一致。

```bat
:: 重建磁盘，保证是干净安装
del "<磁盘>.vmdk"
vmware-vdiskmanager.exe -c -s 30GB -a lsilogic -t 0 "<磁盘>.vmdk"
```

---

## 无 Tools 时如何取证

客机没装 VMware Tools 时，`vmrun` 的客机操作不可用。但**可以用 7-Zip 直接读 VMDK**，把客机磁盘里的日志取出来：

```bat
7z.exe e "<磁盘>.vmdk" -o"<输出目录>" -y "Windows\Panther\UnattendGC\setuperr.log"
7z.exe l "<磁盘>.vmdk" -r "*setuperr.log"     :: 先定位有哪些日志
```

oobeSystem 阶段的日志在 **`Windows\Panther\UnattendGC\`**（不是 `Windows\Panther\`），这是找到根因一的关键。读日志注意编码：这些日志是 UTF-8 带 BOM，用错编码会看到乱码。

---

## 客机侧置备：补丁 + VMware Tools

`FirstLogonCommands` 可以自动执行脚本，但有两点必须处理：

**1. 顺序**：VMware Tools 13.x 的驱动是 SHA-2 签名的，Win7 SP1 原版镜像需要先补齐 SHA-2 支持。所以顺序是：

1. `KB4490628`（服务堆栈更新）→ 2. `KB4474419`（SHA-2 签名支持）→ **重启** → 3. VMware Tools

两个补丁从微软官方 CDN 获取，**文件名内嵌 SHA-1，下载后务必核对**：

```
https://catalog.s.download.windowsupdate.com/c/msdownload/update/software/secu/2019/03/windows6.1-kb4490628-x64_d3de52d6987f7c8bdc2c015dca69eac96047c76e.msu
https://catalog.s.download.windowsupdate.com/c/msdownload/update/software/secu/2019/09/windows6.1-kb4474419-v3-x64_b5614c6cea5cb4e198717789633dca16308ef79c.msu

certutil -hashfile <文件> SHA1   # 应与文件名中的哈希一致
```

**2. 跨重启续跑**：补丁装完要重启，Tools 必须在重启之后再装。用一个"登录自续钩子"实现：

```bat
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v payload /t REG_SZ /d "cmd.exe /c for %%i in (D: E: F: G: H: I: J:) do @if exist %%i\payload.cmd call %%i\payload.cmd auto" /f
```

**3. 判据必须查真实状态，不能靠自建标记文件**：本项目第一版用 `tools.done` 这类标记文件做状态机，结果标记被写了、Tools 却没装上，后续每次启动都判定"无事可做"，永久跳过。改成**直接检查真实状态**后才可靠：

```bat
wmic qfe get HotFixID | findstr /I "KB4474419"      :: 补丁是否真的在
if not exist "%ProgramFiles%\VMware\VMware Tools\vmtoolsd.exe" goto phase2   :: Tools 是否真的在
```

完整实现见 `w7payload.cmd`。

---

## 补完体验指数（Aero 的判定依据）

Win7 的 Aero 需要 WDDM 驱动 + 3D 加速，还需要**体验指数**存在。无人值守安装会跳过体验指数评估；大内存虚拟机应显式限定内存评估缓冲区：

```
> 正在运行: 系统内存性能评估 ''
错误: 缓冲区大小太大。最大值为32MB
```

**绕过办法**（实测有效）：内存子项显式给缓冲区，再用增量模式复用已生成的分项，生成体验指数需要的 `Formal.Assessment`：

```bat
winsat mem -buffersize 32MB
winsat formal -restart never
```

另需确认 3D 加速已开（**这是开关机的设置，需关机后改**）：

```
mks.enable3d = "TRUE"
svga.graphicsMemoryKB = "262144"
```

开启后 `winsat` 的 Direct3D 各项才有结果；关闭时这些项目根本跑不出数字。

## 核验（装完 Tools 之后）

Tools 装好后，`vmrun` 的客机操作提供了程序化核验通道：

```bat
vmrun.exe -T ws -gu <用户> -gp <密码> copyFileFromHostToGuest "<vmx>" "<宿主脚本>" "C:\check.cmd"
vmrun.exe -T ws -gu <用户> -gp <密码> runProgramInGuest "<vmx>" -interactive "C:\Windows\System32\cmd.exe" "/c C:\check.cmd"
vmrun.exe -T ws -gu <用户> -gp <密码> copyFileFromGuestToHost "<vmx>" "C:\check.txt" "<宿主输出>"
```

建议核验项：系统版本、CPU/内存、已装补丁列表、`VMTools` 服务状态、Tools 版本、网卡与 IP、磁盘剩余空间、激活宽限期。

> 提示：命令行引号经 `vmrun` 传递容易被打乱（本项目遇到过 `winsat` 报"不对称的双引号"）。**把命令写进 .cmd 文件再调用**最稳。

---

## 完成判据

- 冷启动直接进入 `User` 桌面，不出现密码框。
- 原安装临时密码无法再用于 VMware 来宾认证。
- `vmrun getGuestIPAddress "<vmx路径>" -wait` 返回来宾 IP，证明 VMware Tools 正常通信。
- `KB4490628`、`KB4474419` 和 `VMTools` 服务均从客机真实状态读取确认。
- `sata0:1`、`sata0:2`、`sata0:3` 均设为 `startConnected = "FALSE"`，启动顺序改为 `hdd,cdrom`。

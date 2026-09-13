# 实测数据与证据

本文汇总全部关键结论的**实测值**与**复核方法**，便于你自己验证，而不是采信结论。

采集环境：Windows 11 专业版（build 26200），VMware Workstation 26H1u1（build 25688693）。

---

## 一、安装包与镜像

| 项目 | 值 |
|---|---|
| Workstation 安装包 | `VMware-Workstation-Full-26H1u1-25688693.exe`，280,609,368 字节 |
| 签名状态 | `Valid`，签署者 `CN=Broadcom Inc`（DigiCert 时间戳） |
| 程序版本 | 26.0.1 build-25688693 |
| 安装包 SHA256 | `3d775c3c2153600eef4642f95d519a514ba7e861400bda2598352bff792db473` |
| 官方发布说明中的条款 | Workstation Pro 对个人、商业与教育用途均免费，**不再需要许可证密钥** |
| Win7 镜像 | `cn_windows_7_ultimate_with_sp1_x64_dvd_u_677408.iso`，3,420,557,312 字节 |
| 镜像 SHA1 | `2ce0b2db34d76ed3f697ce148cb7594432405e23`（与微软 MSDN 官方值一致） |

复核：

```powershell
$s = Get-AuthenticodeSignature '<安装包>'; $s.Status; $s.SignerCertificate.Subject
(Get-Item '<安装包>').VersionInfo.FileVersion
certutil -hashfile '<安装包>' SHA256
certutil -hashfile '<镜像>' SHA1
```

## 二、虚拟机规格实测（客机内读取）

| 项目 | 实测值 | 读取命令（客机内） |
|---|---|---|
| 系统 | Windows 7 旗舰版 SP1，6.1.7601，64 位 | `wmic os get Caption,Version,BuildNumber,OSArchitecture` |
| CPU | 4 逻辑处理器，1 插槽 | `wmic computersystem get NumberOfProcessors,NumberOfLogicalProcessors` |
| 内存 | 8,589,402,112 字节（8 GB） | 同上 `TotalPhysicalMemory` |
| 磁盘 | 30 GB 精简置备，客机内可用约 13.5 GB | `wmic logicaldisk get Caption,Size,FreeSpace` |
| 已装补丁 | KB2534111、KB2999226、**KB4474419**、**KB4490628**、KB976902 | `wmic qfe get HotFixID,InstalledOn` |
| VMware Tools | **13.1.5.0**，`VMTools` 服务 RUNNING | `sc query VMTools` / 读 `vmtoolsd.exe` 文件版本 |
| 网卡 | Intel PRO/1000 MT（e1000），NAT，IP 192.168.54.128 | `ipconfig /all` |
| 激活状态 | 初始宽限期 30 天（未输入密钥） | `cscript //nologo %windir%\System32\slmgr.vbs /xpr` |

3D 加速开启后，`winsat` 才有 Direct3D 结果：Batch 7,067 F/s、Geometry 10,088 F/s、显存吞吐 154,686 MB/s。**关闭 3D 时这些项目跑不出数字** —— 这是判断 3D 是否真的生效的硬指标。

## 三、Win7 无人值守的两个根因

### 根因一：`AdministratorPassword` 不是 Win7 的设置项

客机日志（`Windows\Panther\UnattendGC\setuperr.log`，UTF-8 带 BOM）原文：

```
[oobeldr.exe] SMI data results dump: Source = Name: Microsoft-Windows-Shell-Setup, Language: neutral,
              ProcessorArchitecture: amd64, PublicKeyToken: 31bf3856ad364e35, VersionScope: nonSxS,
              /settings/AdministratorPassword
[oobeldr.exe] SMI data results dump: Description = Setting is not defined in this component.
[oobeldr.exe] User input error was detected in unattend file. Error: [0x0]
[oobeldr.exe] Failed to complete RunSMIPass for oobeSystem.  Error: [0x8030000C]
```

界面只报"无法分析或处理 pass [oobeSystem]……组件或设置不存在"，**不点名是哪一项**。日志才点名 `AdministratorPassword`。

### 根因二：失败后重复"重装"其实没重装

```
[oobeldr.exe] Status for unattend pass [oobeSystem] = 0x1
[oobeldr.exe] Pass has failed status; system is in an invalid state.
```

失败状态入库后，后续启动在**解析应答文件之前**就中止 —— 改应答文件不会有任何效果。

识别方法：oobeSystem 出现在启动后 **34–45 秒**（全新安装需约 5 分钟），说明它恢复的是旧安装。日志时间戳对比即得：

```bat
:: 客机日志里 oobeSystem 的时间点，减去该次启动时间
findstr /C:"RunSMIPass for oobeSystem" "C:\Windows\Panther\UnattendGC\setuperr.log"
```

### 无 Tools 时的取证方法

用 7-Zip 直接读客机磁盘镜像即可取出日志：

```bat
7z.exe l "<磁盘>.vmdk" -r "*setuperr.log"
7z.exe e "<磁盘>.vmdk" -o"<输出目录>" -y "Windows\Panther\UnattendGC\setuperr.log"
```

## 四、winsat 内存子项缺陷

```
> 正在运行: 系统内存性能评估 ''
错误: 缓冲区大小太大。最大值为32MB
```

绕过（实测有效）：

```bat
winsat mem -buffersize 32MB     :: 单独跑内存项，显式给缓冲区
winsat formal -restart never    :: 增量模式复用已有分项，生成体验指数需要的 Formal 评估
```

生成的 `Formal.Assessment (Recent).WinSAT.xml` 含官方分数（本项目实测：基准 7.8、图形 7.9）。注意首次只生成 `(Initial)`，再跑一次才生成 `(Recent)` —— 体验指数页面读的是 `(Recent)`。

## 五、Workstation 汉化相关

### 安装目录 `messages\` 只有三种语言

```
messages\es\   messages\fr\   messages\ja\      ← 无 zh_CN
```

### 词条量对比（26H1）

| 文件 | 词条数 | CJK 字符数 | 备注 |
|---|---|---|---|
| `messages/ja/vmware.vmsg` | 7,073 | 144,727 | 纯文本 |
| `messages/ja/vmui-ja.dll` | 501 串 | 25,875 | 纯资源库，`.text` 仅 86 字节 |
| `messages/ja/vmappsdk-ja.dll` | 57,632 串 | 1,079,530 | 纯资源库，`.text` 仅 86 字节；含 1,017 张 PNG |

### 架构对照（决定成败的关键）

| 文件 | 架构 |
|---|---|
| 26H1 `vmware.exe`（及全部 VMware 组件） | 64 位 |
| 26H1 `vmui-ja.dll` / `vmappsdk-ja.dll` | 64 位 |
| **17.6.4 `vmui-zh_CN.dll` / `vmappsdk-zh_CN.dll`** | **32 位** |
| 26H1 唯一 32 位组件 | `mkisofs.exe`（捆绑第三方工具，不走 VMware 语言机制） |

因此 17.6.4 的中文语言 DLL 在 26H1 上无法加载（日志：`unable to load vmui-zh_CN.dll`）。**而在这两个 DLL 加载失败的情况下，菜单栏依然是中文** —— 说明可见文字来自 `.vmsg`。

复核架构：

```python
import struct
d = open(path, 'rb').read()
pe = struct.unpack_from('<I', d, 0x3c)[0]
print({0x14c: 'x86', 0x8664: 'x64'}[struct.unpack_from('<H', d, pe + 4)[0]])
```

### 语言包质量指标（社区放出的 17.6.4 中文包实测）

| 指标 | 值 |
|---|---|
| 词条数 | 7,294（格式异常 0 行，全 CRLF，UTF-8 无 BOM） |
| 与 ja 目录键交集 | 6,988 / 7,073（98.8%） |
| 本包独有键 | 306 |
| 可与提取的英文原文对照 | 5,753 |
| 两个 DLL 的签名 | `Valid`，签署者 `CN=Broadcom Inc`，时间戳 DigiCert Timestamp 2024 |

### 英文原文的分布（hashdata 标记命中数）

| 文件 | 条数 |
|---|---|
| `x64\vmware-vmx.exe` | 2,162 |
| `vmwarecui.dll` | 1,824 |
| `vmwarebase.dll` | 1,636 |
| `vix.dll` | 1,480 |
| `vmcli.exe` | 1,378 |
| `vmwarewui.dll` | 1,252 |
| 合计唯一词条 | **5,903**；与 ja 目录交集 **5,831** |

### 汉化生效的日志证据

```
DICT               pref.locale = "zh_CN"
LOCALE GBK -> NULL User=804 System=804
Msg_SetLocaleEx: HostLocale=GBK UserLocale=zh_CN
```

### 界面语言的实际核验（无障碍树读取）

```
[68] menuitem 文件(F)     [67] menuitem 编辑(E)     [66] menuitem 查看(V)
[65] menuitem 虚拟机(M)   [64] menuitem 选项卡(T)   [63] menuitem 帮助(H)
[15] button  我的计算机
```

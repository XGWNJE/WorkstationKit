# 获取渠道与校验方法

本仓库**不存放任何安装包或二进制**，全部按下表自行获取。每个条目都给出**官方入口**与**校验方法** —— 校验这一步不能省，它是判断"拿到的是不是原厂文件"的唯一手段。

> 标注说明：**已核验** = 整理者实测可达或实测校验值；**需登录** = 官方渠道需免费账号；**动态页** = 页面内容由脚本加载，抓取工具看不到列表，需用浏览器打开。
>
> 链接可用性会变，尤其第三方镜像。核验日期：2026-09-13。

---

## 一、VMware Workstation 本体（26H1u1）

| 项目 | 内容 |
|---|---|
| 官方入口 | **Broadcom 支持门户** → https://support.broadcom.com （需登录，动态页） |
| 操作路径 | 登录后：下拉选 **VMware Cloud Foundation** → 左侧 **My Downloads** → **Free Software Downloads available HERE** → 搜 `Workstation` → 选版本 → 先点 **Terms and Conditions** 链接才能勾选同意 → 下载 |
| 文件名 | `VMware-Workstation-Full-26H1u1-25688693.exe` |
| 版本说明（官方，已核验） | https://techdocs.broadcom.com/us/en/vmware-cis/desktop-hypervisors/workstation-pro/26H1/release-notes/vmware-workstation-pro-26h1u1-release-notes.html |
| 发布说明索引（已核验） | https://techdocs.broadcom.com/us/en/vmware-cis/desktop-hypervisors/workstation-pro/26H1/release-notes.html |
| 产品页（已核验可达） | https://www.vmware.com/products/desktop-hypervisor/workstation-and-fusion |
| 许可条款 | 官方发布说明原文：Workstation Pro 对个人、商业与教育用途**均免费**，**不再需要许可证密钥** |

**校验（必做）** —— 本机实测值：

```
文件大小  280,609,368 字节
程序版本  26.0.1 build-25688693
签名状态  Valid，签署者 CN=Broadcom Inc（DigiCert 时间戳）
SHA256    3d775c3c2153600eef4642f95d519a514ba7e861400bda2598352bff792db473
```

```powershell
$s = Get-AuthenticodeSignature '<安装包>'
$s.Status; $s.SignerCertificate.Subject          # 期望 Valid / CN=Broadcom Inc
(Get-Item '<安装包>').VersionInfo.FileVersion    # 期望 26.0.1
certutil -hashfile '<安装包>' SHA256              # 对比上面的 SHA256
```

> 提示：Broadcom 早期曾有无需登录的 CDN 直链，现已被关闭。第三方 GitHub 仓库确有转存官方安装包的，但**同一仓库常夹带序列号/keygen** —— 那部分不要碰，且第三方转存可用上面的签名与 SHA256 自行判定真伪。

## 二、Windows 7 旗舰版 SP1 x64 镜像

| 项目 | 内容 |
|---|---|
| 官方状态 | 微软已停止分发 Win7 下载，无官方直链 |
| 文件名 | `cn_windows_7_ultimate_with_sp1_x64_dvd_u_677408.iso` |
| 权威校验值 | **SHA1 `2ce0b2db34d76ed3f697ce148cb7594432405e23`**（微软 MSDN 官方值，整理者已实测比对一致） |
| 文件大小 | 3,420,557,312 字节 |
| 常见来源 | 各类 MSDN 原版镜像索引站（如 `msdn.itellyou.cn` / `next.itellou.cn` 一类，动态页）。这些是非官方镜像站，**必须靠下面的 SHA1 自证** |

**校验（必做）**：

```bat
certutil -hashfile "cn_windows_7_ultimate_with_sp1_x64_dvd_u_677408.iso" SHA1
```

期望输出 `2ce0b2db34d76ed3f697ce148cb7594432405e23`。**不一致就不要用** —— 镜像被改动过（哪怕只是删掉 `sources\ei.cfg` 解锁版本选择，哈希也会变）。

> 该镜像内含 4 个版本，索引为：1 家庭普通版 / 2 家庭高级版 / 3 专业版 / 4 旗舰版。可用
> `dism /Get-WimInfo /WimFile:<盘>:\sources\install.wim` 自行核对。

## 三、Win7 前置补丁（Tools 安装的前提）

这两个补丁是**官方直链**，且**文件名内嵌 SHA-1**，下载后逐字比对即可确认：

| 补丁 | 用途 | 直链（微软官方 CDN） |
|---|---|---|
| KB4490628 x64 | 服务堆栈更新（KB4474419 的前提） | `https://catalog.s.download.windowsupdate.com/c/msdownload/update/software/secu/2019/03/windows6.1-kb4490628-x64_d3de52d6987f7c8bdc2c015dca69eac96047c76e.msu` |
| KB4474419 v3 x64 | SHA-2 代码签名支持（Tools 13.x 的前提） | `https://catalog.s.download.windowsupdate.com/c/msdownload/update/software/secu/2019/09/windows6.1-kb4474419-v3-x64_b5614c6cea5cb4e198717789633dca16308ef79c.msu` |

官方目录页（可用浏览器搜到同一文件）：

- https://www.catalog.update.microsoft.com/Search.aspx?q=KB4490628
- https://www.catalog.update.microsoft.com/Search.aspx?q=KB4474419

**校验**（文件名里的哈希就是期望值）：

```bat
certutil -hashfile kb4490628-x64.msu SHA1        :: 期望 d3de52d6987f7c8bdc2c015dca69eac96047c76e
certutil -hashfile kb4474419-v3-x64.msu SHA1     :: 期望 b5614c6cea5cb4e198717789633dca16308ef79c
```

> 备选：宿主经代理访问 `download.windowsupdate.com` 可能 TLS 握手失败（实测遇到 `SEC_E_WRONG_PRINCIPAL`），改用上面的 `catalog.s.download.windowsupdate.com` 走 HTTPS 正常。

## 四、VMware Tools

**不需要单独下载** —— Workstation 安装目录自带：

```
<安装目录>\windows.iso        # 26H1 内置版本为 13.1.5
```

置备脚本会自动挂载它并静默安装。装完可用以下方式确认版本：

```bat
reg query "HKLM\SOFTWARE\VMware, Inc.\VMware Tools" /v ProductVersion
:: 或读文件版本
powershell -c "(Get-Item 'C:\Program Files\VMware\VMware Tools\vmtoolsd.exe').VersionInfo.FileVersion"
```

> 注意：Tools 13.x 在 Win7 上**必须先装 KB4474419**，否则驱动签名校验失败。顺序不能颠倒。

## 五、Workstation 界面中文语言文件

本仓库**不转发**这些文件（版权与上游许可原因），请自行获取。**无论从哪拿到，都要先验签。**

### 途径 A：从官方 17.6.x 安装包提取（最干净）

17.6.4 是最后一个带中文的版本。从 Broadcom 门户按第一节的路径选 **17.6.x** 下载安装包（或只解包），取出：

```
messages\zh_CN\vmui-zh_CN.dll
messages\zh_CN\vmappsdk-zh_CN.dll
messages\zh_CN\vmware.vmsg
```

> 官方 17.6.x 入口：https://support.broadcom.com （需登录，动态页；搜索 `Workstation` 后在版本列表里选 17.6.x）

### 途径 B：社区已提取好的成品

社区已有把 17.6.4 的 `zh_CN` 提取放出的仓库，例如（**已核验可达，整理者实测从中取得文件**）：

- https://github.com/Kuroba-Sayuki/VMware-Workstation-Chinese-Localization
  - 语言文件在该仓库的 `VMware Workstation Messages/zh_CN/` 目录下
  - 该仓库自述为「**禁止二次分发，仅作学习＆存档使用**」—— 自用可以，**不要再转发**
- 另有若干镜像（Gitee / GitCode 上的同名项目、网盘等），可用性变动较大

### 校验（不可省）

两个 DLL 是会被载入进程的二进制，**带 Broadcom 数字签名**，验签能一击判真伪（篡改必破坏签名，而重签需要 Broadcom 私钥）：

```powershell
foreach ($f in @('vmui-zh_CN.dll','vmappsdk-zh_CN.dll')) {
  $s = Get-AuthenticodeSignature -LiteralPath $f
  '{0}: {1} / {2}' -f $f, $s.Status, $s.SignerCertificate.Subject
}
```

期望：

```
Status : Valid
签署者 : CN=Broadcom Inc, O=Broadcom Inc, ...
颁发者 : CN=DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1
时间戳 : CN=DigiCert Timestamp 2024
```

本机实测的两个文件校验值（可与你的比对）：

```
vmui-zh_CN.dll      169,336 字节   SHA256 8F9B003AC4651121F1A5D401E5E1564DBA6C43DE1A3E10184A8FD2BF9698415A
vmappsdk-zh_CN.dll  14,054,776 字节  SHA256 03B59EE53C2AFB86B87788BB723C410B984893A13C3E7BD8CF334A877FBD07D1
```

`vmware.vmsg` 是纯文本无签名，用本仓库脚本校验结构与覆盖率：

```bat
python workstation-zhcn\tools\verify-language-pack.py <vmware.vmsg路径> "<安装目录>\messages\ja\vmware.vmsg"
```

本机实测该成品：7,294 条、格式异常 0 行、与 ja 目录键交集 6,988/7,073（98.8%）、全 CRLF、UTF-8 无 BOM。

> **重要**：这两个 DLL 是 **32 位**，在 64 位 26H1 上无法加载 —— 但**不影响使用**，界面中文由 `vmware.vmsg` 提供（实测删除 DLL 后菜单栏仍为中文）。放入后若日志报 `unable to load`，属正常现象。

## 六、汇总表

| 需要的东西 | 获取方式 | 校验 |
|---|---|---|
| Workstation 26H1u1 安装包 | Broadcom 门户（需登录） | Authenticode 签名 + SHA256 |
| Win7 旗舰版 SP1 x64 镜像 | MSDN 原版镜像站 | **SHA1** 比对 |
| KB4490628 / KB4474419 | 微软官方 CDN 直链 | 文件名内嵌 SHA-1 |
| VMware Tools | Workstation 自带 `windows.iso` | 版本号 13.1.5 |
| 中文语言文件 | 官方 17.6.x 安装包提取，或社区成品 | **Authenticode 签名（Broadcom）** |

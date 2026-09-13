# 网盘资源包清单

本文件是夸克网盘分享包 `WorkstationKit-资源包` 的内容清单，**与包内那份《说明与校验》内容一致**。放在这里是为了让它随仓库受版本控制、便于核对与追溯。

分享地址见 [downloads.md](downloads.md) 的「最省事：网盘镜像」一节。

---

## 一、包里有什么

| 文件 | 说明 |
|---|---|
| `VMware-Workstation-Full-26H1u1-25688693.exe` | Workstation 26H1u1 官方安装包（Windows）。官方对个人、商业与教育用途均免费，不需要许可证密钥 |
| `语言文件\vmui-zh_CN.dll`<br>`语言文件\vmappsdk-zh_CN.dll`<br>`语言文件\vmware.vmsg` | Workstation 界面中文语言文件，取自 17.6.4（最后一个带中文的版本）。用法见 [workstation-zhcn.md](workstation-zhcn.md) |
| `cn_windows_7_ultimate_with_sp1_x64_dvd_u_677408.iso` | Windows 7 旗舰版 SP1 x64 原版镜像（微软 MSDN 原版，未经改动），约 3.2 GB。内含 4 个版本，索引为 1 家庭普通版 / 2 家庭高级版 / 3 专业版 / 4 旗舰版。系统已停止支持，仅供本地测试与实验环境 |

## 二、大小与校验值

| 文件 | 大小（字节） | 校验值 |
|---|---:|---|
| `VMware-Workstation-Full-26H1u1-25688693.exe` | 280,609,368 | SHA256 `3D775C3C2153600EEF4642F95D519A514BA7E861400BDA2598352BFF792DB473` |
| `语言文件\vmui-zh_CN.dll` | 169,336 | SHA256 `8F9B003AC4651121F1A5D401E5E1564DBA6C43DE1A3E10184A8FD2BF9698415A` |
| `语言文件\vmappsdk-zh_CN.dll` | 14,054,776 | SHA256 `03B59EE53C2AFB86B87788BB723C410B984893A13C3E7BD8CF334A877FBD07D1` |
| `语言文件\vmware.vmsg` | 617,586 | SHA256 `1B0D67EC612C1EE3999D6E739363E191654F02BB699CAD9D4868EB72FD526C7D` |
| `cn_windows_7_ultimate_with_sp1_x64_dvd_u_677408.iso` | 3,420,557,312 | **SHA1** `2CE0B2DB34D76ED3F697CE148CB7594432405E23`（微软 MSDN 官方值，镜像的权威判据）<br>SHA256 `70CDFB0CDCBEB2659163E9417D5C242B37AE564DA810E7DA21DAC5C8492AB72F` |

## 三、怎么校验

```bat
:: 哈希
certutil -hashfile "VMware-Workstation-Full-26H1u1-25688693.exe" SHA256
certutil -hashfile "语言文件\vmui-zh_CN.dll" SHA256
certutil -hashfile "语言文件\vmappsdk-zh_CN.dll" SHA256
certutil -hashfile "cn_windows_7_ultimate_with_sp1_x64_dvd_u_677408.iso" SHA1
certutil -hashfile "cn_windows_7_ultimate_with_sp1_x64_dvd_u_677408.iso" SHA256
```

```powershell
# 数字签名：两个语言 DLL 是会被载入进程的二进制，务必验签
Get-AuthenticodeSignature '语言文件\vmui-zh_CN.dll' |
    Select-Object Status, @{n='Signer';e={$_.SignerCertificate.Subject}}
```

期望 `Status` 为 `Valid`、签署者为 `CN=Broadcom Inc`。被篡改必然验签失败，而重新签名需要 Broadcom 的私钥 —— 所以验签能一击判真伪。

## 四、几点须知

1. **官方为什么没有中文**：Broadcom 从 Workstation 25H2 起移除了简繁中文，官方现只支持英语、法语、日语、西班牙语。这里是沿用旧版语言文件的移植方案，属**不受支持**的配置。
2. **那两个 DLL 在新版上加载不了，是正常的**：它们是 32 位，而 26H1 的界面进程是 64 位。不影响使用 —— 界面中文由纯文本的 `vmware.vmsg` 提供，菜单栏也是。日志里出现 `unable to load vmui-zh_CN.dll` 可以忽略。
3. **词条来自 17.6.4**：Broadcom 在更新版本里新增的界面文字没有中文，会回落到英文。
4. **升级会冲掉**：Workstation 升级后 `messages\zh_CN\` 可能被清掉，需要重放一次。
5. **版权**：安装包与语言文件均为 Broadcom 的软件与二进制，请自行确认使用方式；本资源包仅为方便获取而汇总，与 Broadcom 无关联、未获其背书。

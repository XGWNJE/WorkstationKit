# VMware Workstation 界面汉化（25H2 / 26H1）

官方从 **Workstation 25H2 起移除了简繁中文**。本文记录实测可行的恢复方案，以及几个反直觉的实测结论。

> **受支持状态**：这是**不受支持**的配置。Workstation 更新后 `messages\zh_CN\` 可能被清掉，需重放。

---

## 一、现状：中文是被官方删掉的，不是配置问题

Broadcom 从 25H2 起有意移除中文，理由是与 VCF/vSphere 的语言集对齐。当前官方只支持**英语、法语、日语、西班牙语**。

在安装目录里可直接验证这一点：

```
<安装目录>\messages\
    es\      ← 西班牙语
    fr\      ← 法语
    ja\      ← 日语
```

**没有 `zh_CN` 目录**，也没有任何中文资源。所以"在设置里找语言选项"这条路不存在 —— 资源文件本身被删了。

## 二、汉化机制

界面语言由两件事决定：

1. **偏好** `%APPDATA%\VMware\preferences.ini` 里的 `pref.locale`
2. **资源** `<安装目录>\messages\<locale>\vmware.vmsg`

设置后可用日志确认是否生效（`%TEMP%\vmware-<用户>\vmware-ui-<pid>.log`）：

```
DICT               pref.locale = "zh_CN"
Msg_SetLocaleEx: HostLocale=GBK UserLocale=zh_CN
```

看到 `UserLocale=zh_CN` 就说明偏好已被接受。

激活方式三选一：

- **偏好文件**（推荐）：`pref.locale = "zh_CN"`
- **快捷方式参数**：目标末尾追加 `--locale zh_CN`
- 两者可同时使用，不冲突

## 三、几个反直觉的实测结论

### 结论 1：整界面（含菜单栏）由纯文本 `.vmsg` 提供

`vmware.vmsg` 是**纯文本**的 `键 = "值"` 表，UTF-8、CRLF。**菜单栏 `文件/编辑/查看/虚拟机/选项卡/帮助` 都来自它**。

实测方式：无障碍树读取真实界面文字 ——

```
[68] menuitem 文件(F)     [67] menuitem 编辑(E)     [66] menuitem 查看(V)
[65] menuitem 虚拟机(M)   [64] menuitem 选项卡(T)   [63] menuitem 帮助(H)
```

### 结论 2：那两个语言 DLL **不需要**（新版上根本加载不了）

`messages\<locale>\` 下通常还有 `vmui-<locale>.dll` 与 `vmappsdk-<locale>.dll`。实测：

| 文件 | 架构 |
|---|---|
| 17.6.4 的 `vmui-zh_CN.dll` / `vmappsdk-zh_CN.dll` | **32 位 (x86)** |
| 26H1 自带的 `vmui-ja.dll` / `vmappsdk-ja.dll` | 64 位 (x64) |
| 26H1 的 `vmware.exe`（以及全部 VMware 组件） | **64 位 (x64)** |

**32 位 DLL 无法载入 64 位进程**，日志明确记录：

```
wui::util::LoadLanguageDLL: unable to load vmui-zh_CN.dll
wui::util::LoadLanguageDLL: unable to load vmappsdk-zh_CN.dll
```

而且 —— **在这两个 DLL 加载失败的情况下，菜单栏依然是中文**。删除它们、重启复核，界面照样全中文。

原因：17.6 是最后一个带中文的版本，而它的 UI 是 32 位；25H2 起 UI 变 64 位时中文已被移除。**"64 位的中文语言 DLL"从未存在过**，所以不必去找。

> 26H1 里唯一 32 位组件是捆绑的第三方 `mkisofs.exe`，它不走 VMware 语言机制。

### 结论 3：语言文件在哪个目录名下生效

实测 `messages\zh_CN\` 是正确名称（与日志中的 `UserLocale=zh_CN` 对应）。曾试过 `zh`、`zh-CN` 两种目录名，均不生效 —— 不需要尝试它们。

---

## 四、获取与验签（关键步骤）

本仓库**不重新分发**语言文件（版权与上游许可原因）。你需要自己获取。**无论从哪里拿到，都要先验签。**

> 最省事的是**网盘镜像**（安装包与语言文件都在里面，免注册）；完整获取入口与校验值见 **[downloads.md](downloads.md)**。下面是要点。

### 从哪里获取

- **官方（最干净）**：从 Broadcom 支持门户下载 **17.6.x** 安装包（需免费账号），17.6.4 是最后一个带中文的版本。取出其中的 `messages\zh_CN\` 三个文件即是原厂文件。
  入口：https://support.broadcom.com → 登录 → 搜 `Workstation` → 在版本列表选 **17.6.x**
- **社区成品（已核验可达）**：已有整理好的 17.6.4 `zh_CN` 放在 GitHub：
  **https://github.com/Kuroba-Sayuki/VMware-Workstation-Chinese-Localization**
  语言文件位于该仓库的 `VMware Workstation Messages/zh_CN/` 目录。
  **注意其自述为「禁止二次分发，仅作学习＆存档使用」** —— 自用可以，别再转发。

### 必须做的验签

语言 DLL 是会被载入进程的二进制，来源必须核验。**这两个 DLL 带 Broadcom 的数字签名**，所以验签能一击判真伪 —— 被篡改必然验签失败，而重新签名需要 Broadcom 的私钥。

```powershell
foreach ($f in @('vmui-zh_CN.dll','vmappsdk-zh_CN.dll')) {
  $s = Get-AuthenticodeSignature -LiteralPath $f
  '{0}: {1} / {2}' -f $f, $s.Status, $s.SignerCertificate.Subject
}
```

期望结果：

```
Status   : Valid
签署者   : CN=Broadcom Inc, O=Broadcom Inc, ...
颁发者   : CN=DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1
时间戳   : CN=DigiCert Timestamp 2024
```

`vmware.vmsg` 是纯文本、无签名。它是文本而非代码，风险远低于 DLL；可用本仓库的校验脚本检查结构与占比：

```bat
python workstation-zhcn\tools\verify-language-pack.py <vmware.vmsg路径> [ja目录的vmware.vmsg]
```

该脚本会报出：词条数、格式异常行数、CRLF/编码、与 ja 目录的键交集覆盖率、助记符与占位符规范性。

---

## 五、安装

1. 把 `zh_CN` 目录（含 `vmware.vmsg`）放入：

   ```
   <安装目录>\messages\zh_CN\
   ```

   26H1 的安装目录通常是 `C:\Program Files\VMware\VMware Workstation`（**不是** `Program Files (x86)`）。

2. 写入偏好（先备份 `preferences.ini`）：

   ```
   pref.locale = "zh_CN"
   ```

3. **完全退出并重启 Workstation**（`vmware.exe`；建议连 `vmware-tray.exe` 一起结束）。

4. 核验：菜单栏应显示为 `文件(F) / 编辑(E) / 查看(V) / 虚拟机(M) / 选项卡(T) / 帮助(H)`；`%TEMP%` 下的 UI 日志应出现 `UserLocale=zh_CN`。

> 文件"正在使用"而无法覆盖时，先结束 `vmware.exe` 与 `vmware-tray.exe`。

## 六、回退

删除 `messages\zh_CN\` 目录，并移除 `preferences.ini` 中的 `pref.locale` 一行，重启即可还原为英文。

## 七、限制

- **词条来自 17.6.4**：Broadcom 在 25H2/26H1 新增的界面文字**没有中文**，会回落到英文。
- **不受支持**：非官方配置，出现异常请先回退再排查。
- **更新会被冲掉**：Workstation 升级后可能需要重放。
- **关于"关于"页**：版本号显示的是实际安装版本，可能与语言文件所属版本不一致，属正常现象。

## 八、想让中文更全？可以自己续译

`.vmsg` 是纯文本，可自行补充或修订词条；英文原文可以从安装目录的二进制里提取（它们以 `@&!*@*@(键)英文值` 的 "hashdata" 表内嵌在 `vmware.exe`、`vmwarebase.dll`、`vmwarecui.dll`、`vmwarewui.dll` 等文件中）。

- 格式规范与助记符/占位符约定：[../workstation-zhcn/catalog-format.md](../workstation-zhcn/catalog-format.md)
- 英文原文提取脚本：[../workstation-zhcn/tools/extract-english-catalog.py](../workstation-zhcn/tools/extract-english-catalog.py)

实测数据（26H1）：`messages/ja/vmware.vmsg` 有 7,073 条；提取到的英文词条 5,903 条，其中 **5,831 条**可与 ja 目录对齐 —— 即绝大多数词条都能拿到英文原文作为翻译底稿。

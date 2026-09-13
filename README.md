# WorkstationKit

VMware Workstation 26H1 的两件事的**整理笔记与配套工具**：

1. **Windows 7 无人值守安装** —— 从建虚拟机到装完补丁与 VMware Tools，全程无需人工干预。
2. **Workstation 界面汉化** —— 官方在 25H2 移除了中文，这里记录已实测可行的恢复方案。

> **整理与维护**：[@XGWNJE](https://github.com/XGWNJE)
>
> 本仓库只做**整理**：流程、配方、格式规范与自研脚本。**不重新分发任何第三方安装包或二进制**（原因见下）。

---

## 这个仓库解决什么问题

| 问题 | 本仓库给出的东西 | 入口 |
|---|---|---|
| Win7 无人值守安装总在 OOBE 阶段失败，报错含糊 | 两个真实根因的定位过程与修法 | [docs/win7-unattended-install.md](docs/win7-unattended-install.md) |
| 客机没装 Tools 时，怎么读客机日志排查？ | 用 7-Zip 直接读 VMDK 取 `setuperr.log` | 同上「无 Tools 时如何取证」 |
| Win7 的体验指数（Aero 判定依据）从未生成 | `winsat` 内存子项缓冲区缺陷的绕过办法 | 同上「补完体验指数」 |
| Workstation 26H1 界面没有中文 | 汉化机制、成品获取、**验签**、安装与回退 | [docs/workstation-zhcn.md](docs/workstation-zhcn.md) |
| 17.6.4 的语言文件在新版上加载失败 | x86/x64 架构冲突的实测结论 | 同上「为什么那两个 DLL 不需要」 |
| 想自己续译界面文字 | 词条格式规范 + 英文原文提取脚本 | [workstation-zhcn/catalog-format.md](workstation-zhcn/catalog-format.md) |

## 目录

```
docs/
  downloads.md                  获取渠道与校验方法（官方入口 + 直链 + 逐项校验值）
  win7-unattended-install.md    Win7 无人值守安装完整流程（含两个根因）
  workstation-zhcn.md           Workstation 界面汉化的完整方案
  verified-facts.md             实测数据与证据（含核验命令，便于你自己复核）
win7-unattend/
  Autounattend.xml              应答文件（密码已脱敏为占位符）
  w7payload.cmd                 分阶段置备脚本（补丁 + Tools，幂等）
  reference.vmx                 虚拟机配置参考（路径已脱敏）
workstation-zhcn/
  catalog-format.md             词条文件格式规范（逆向所得，含英文原文藏匿位置）
  tools/extract-english-catalog.py   从二进制提取英文原文字典
  tools/verify-language-pack.py      校验语言包结构、覆盖率与占位符
```

## 明确不包含什么

**不含 VMware Workstation 安装包，也不含任何语言文件（`*.dll` / `*.vmsg`）。** 三个理由：

1. **版权**：安装包与语言文件是 Broadcom 的专有软件与二进制，公开重新分发属侵权。
2. **上游明确禁止**：社区的语言文件提取仓库自述「禁止二次分发，仅作学习＆存档使用」。转发它既违约，也可能让你的账号被牵连。
3. **技术上也放不进来**：安装包 267 MB，超过 GitHub 单文件 100 MB 上限。

**替代做法**：**[docs/downloads.md](docs/downloads.md) 给出每个部件的具体获取入口与校验值** —— 包括官方直链、需登录渠道的操作路径，以及逐项校验方法（文件哈希、数字签名）。

校验这一步不能省：**它让"用别人放出来的成品"变成可核验的动作，而不是盲信。** 本仓库所有结论都附实测值，拿到文件后你都能自己复核一遍。

## 已核验的关键结论（先行摘要）

| 结论 | 依据 |
|---|---|
| Win7 的 oobeSystem **不支持** `AdministratorPassword`（那是 Win8+ 的设置项） | 客机 `UnattendGC\setuperr.log` 点名该设置项；`0x8030000C` |
| 失败后重复"重装"其实没重装 | oobeSystem 失败状态被写入注册表，且光盘"按任意键"超时后回落硬盘恢复旧安装 |
| Workstation 汉化靠 `pref.locale` + `messages\<locale>\vmware.vmsg` | 日志 `Msg_SetLocaleEx: UserLocale=zh_CN`；日语对照实验 |
| **菜单栏来自 `.vmsg`，不是那两个语言 DLL** | 两个 DLL 加载失败时菜单栏仍为中文 |
| 17.6.4 的语言 DLL 是 **32 位**，无法载入 64 位 26H1 | PE 头实测：x86 vs 26H1 的 x64 |
| 纯文本 `.vmsg` 即可实现整界面（含菜单栏）中文 | 删除两个 DLL 后重启复核 |

## 许可与归属

- 本仓库的**文档与脚本**为整理者原创，可自由参考；如需明确的开源许可请提 issue。
- 仓库**不包含** Broadcom 的任何二进制或安装包。`VMware`、`VMware Workstation` 是 Broadcom Inc. 的商标，本仓库与 Broadcom 无关联、未获其背书。
- 汉化属**不受支持**的配置；Workstation 更新后可能需要重放。

## 来源与致谢

- **Broadcom / VMware** —— VMware Workstation 本体与 17.6.4 的中文语言文件（语言文件即从那时的官方安装包提取）。
- **社区提取仓库** —— 现成的 `zh_CN` 语言文件由社区整理放出（本仓库只引用其获取途径，不转发文件）。
- 其余流程、逆向所得的格式规范与脚本，来自本仓库整理者在真机上的实测。

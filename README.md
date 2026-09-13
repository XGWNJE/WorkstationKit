# WorkstationKit

VMware Workstation 26H1 的两件事，我踩过坑之后整理在这儿：

1. **Windows 7 无人值守安装** —— 建好虚拟机、挂上应答光盘，剩下全自动，不用守着看。
2. **Workstation 界面汉化** —— 官方从 25H2 起删掉了中文，这里是一套实测能用的恢复办法。

整理：[XGWNJE](https://github.com/XGWNJE)

## 直接下载（省事版）

不想注册 Broadcom 账号、也不想满网找镜像的话，文件我传夸克网盘了（安装包 + 中文语言文件 + Win7 系统镜像）：

https://pan.quark.cn/s/3577e8370038　　提取码：`xLms`

包里附了校验清单（[仓库里也有一份](docs/netdisk-manifest.md)）。**建议还是对一下哈希、验一下签名**再装，方法见 [docs/downloads.md](docs/downloads.md)。

## 文档

| 想看什么 | 去哪 |
|---|---|
| 全自动装 Win7 | [docs/win7-unattended-install.md](docs/win7-unattended-install.md) |
| 界面汉化 | [docs/workstation-zhcn.md](docs/workstation-zhcn.md) |
| 东西从哪拿、怎么确认没被动过 | [docs/downloads.md](docs/downloads.md) |
| 我测出来的数、复核命令 | [docs/verified-facts.md](docs/verified-facts.md) |

## 先说两个坑

这两个是花时间最多的地方，报错都含糊，所以拎到前面来。

**一、Win7 的应答文件里不能写 `AdministratorPassword`。** 那是 Windows 8 以后才有的设置项，写进 Win7 会让整个 OOBE 阶段以 `0x8030000C` 挂掉，而界面只说"组件或设置不存在"，不告诉你是哪一项。日志里才点名。

**二、装失败以后再"重装"，其实没重装。** 失败状态会写进注册表，之后每次启动在解析应答文件之前就中止；而且 Win7 光盘"按任意键"超时后会回到硬盘，接着装那个半成品。所以改完应答文件重跑，什么都没变。判断办法：看 OOBE 阶段出现在开机后多久 —— 全新安装要 5 分钟左右，30 秒就到了那肯定没重装。

## 目录

```
win7-unattend/     应答文件（密码是占位符，记得自己改）、置备脚本、虚拟机配置参考
workstation-zhcn/  词条格式说明、英文原文提取脚本、语言包校验脚本
docs/              上面那几篇文档
```

## 仓库里没有安装包

只放流程和脚本，不放安装包和语言文件。原因就三条：版权是 Broadcom 的、原提取仓库写明"禁止二次分发"、安装包 267 MB 超过 GitHub 单文件上限。

要文件走上面那个网盘链接，或者按 [docs/downloads.md](docs/downloads.md) 自己从官方渠道拿。

## 几个得知道的限制

- 汉化是**不受支持**的玩法，Workstation 升级后可能要重放一次。
- 语言文件是 17.6.4 的，新版新增的界面文字没有中文，会显示英文。
- 那两个 DLL 是 32 位的，在新版 64 位界面里加载不了 —— **这是正常的，不影响**，中文由纯文本的 `vmware.vmsg` 提供，菜单栏也是。
- `VMware` 是 Broadcom 的商标，这个仓库与 Broadcom 无关，也未获其背书。

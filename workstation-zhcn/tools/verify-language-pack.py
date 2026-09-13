#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 VMware Workstation 语言包（vmware.vmsg）。

检查项:
    1. 编码与行尾（期望 UTF-8 无 BOM + CRLF）
    2. 每行是否符合 `键 = "值"` 结构
    3. 词条数与命名空间分布
    4. （可选）与参照语言包（如官方 ja）的键交集覆盖率
    5. （可选）助记符与占位符规范性

用法:
    python verify-language-pack.py <待校验的 vmware.vmsg> [参照的 vmware.vmsg]

示例:
    python verify-language-pack.py "C:\\Program Files\\VMware\\VMware Workstation\\messages\\zh_CN\\vmware.vmsg" ^
                                   "C:\\Program Files\\VMware\\VMware Workstation\\messages\\ja\\vmware.vmsg"

说明:
    语言 DLL（vmui-*.dll / vmappsdk-*.dll）是二进制，验真伪请用数字签名：
        Get-AuthenticodeSignature -LiteralPath <dll>   # 期望 Valid 且签署者为 Broadcom
"""

import collections
import io
import os
import re
import sys

LINE_RE = re.compile(r'^[A-Za-z0-9_.]+ = ".*"$')
MNEMONIC_EN = re.compile(r'[_&]([A-Za-z0-9])')
MNEMONIC_ZH = re.compile(r'[(（][_&]([A-Za-z0-9])[)）]')
PH_EN = re.compile(r'%[sd]')
PH_ZH = re.compile(r'%\d+\$[sd]')


def load(path):
    raw = open(path, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    crlf = raw.count(b'\r\n')
    lone_lf = raw.count(b'\n') - crlf
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError as e:
        print('  !! 不是合法 UTF-8: %s' % e)
        text = raw.decode('utf-8', 'replace')

    entries, bad = {}, []
    for line in text.splitlines():
        line = line.rstrip('\r')
        if not line.strip():
            continue
        if LINE_RE.match(line):
            k, v = line.split(' = "', 1)
            entries[k] = v[:-1]
        else:
            bad.append(line)
    return dict(bom=bom, crlf=crlf, lone_lf=lone_lf,
                entries=entries, bad=bad)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    target = sys.argv[1]
    if not os.path.isfile(target):
        print('文件不存在: %s' % target)
        return 1

    print('=== %s ===' % target)
    a = load(target)
    print('  大小        : %d 字节' % os.path.getsize(target))
    print('  BOM         : %s' % ('有（建议去掉）' if a['bom'] else '无 ✓'))
    print('  CRLF 行数   : %d' % a['crlf'])
    print('  裸 LF 行数  : %d %s' % (a['lone_lf'], '' if a['lone_lf'] == 0 else '（建议统一为 CRLF）'))
    print('  词条数      : %d' % len(a['entries']))
    print('  格式异常行  : %d %s' % (len(a['bad']), '✓' if not a['bad'] else ''))
    for b in a['bad'][:5]:
        print('      BAD: %s' % b[:100])

    pref = collections.Counter(k.split('.')[0] + '.' for k in a['entries'])
    print('  命名空间    : %s' % ', '.join('%s=%d' % (p, n) for p, n in pref.most_common()))

    # 占位符换算：本包位置式 vs 参照包 printf 式（需参照包）
    if len(sys.argv) > 2:
        ref = sys.argv[2]
        if os.path.isfile(ref):
            print()
            print('=== 与参照包对比: %s ===' % ref)
            b = load(ref)
            sk, rk = set(a['entries']), set(b['entries'])
            inter = sk & rk
            print('  参照词条数  : %d' % len(rk))
            print('  交集        : %d' % len(inter))
            print('  覆盖率      : %.1f%%' % (100.0 * len(inter) / max(1, len(rk))))
            only = sk - rk
            print('  本包独有    : %d%s' % (len(only), '' if not only else '（如为新增词条属正常）'))
            missing = rk - sk
            if missing:
                print('  参照有而本包无: %d 条，例如：' % len(missing))
                for k in sorted(missing)[:8]:
                    print('      %s' % k)

            mismatch = []
            for k in sorted(inter):
                n_en = len(PH_EN.findall(b['entries'][k]))
                n_zh = len(PH_ZH.findall(a['entries'][k]))
                if n_en != n_zh:
                    mismatch.append((k, n_en, n_zh))
            print('  占位符数量不匹配: %d %s' % (len(mismatch), '✓' if not mismatch else ''))
            for k, n_en, n_zh in mismatch[:8]:
                print('      %s: 参照=%d 本包=%d' % (k, n_en, n_zh))

    # 助记符抽查
    zh_mn = [k for k, v in a['entries'].items() if MNEMONIC_ZH.search(v)]
    en_mn_inline = [k for k, v in a['entries'].items()
                    if MNEMONIC_EN.search(v) and not MNEMONIC_ZH.search(v)]
    print()
    print('  含括号助记符(译文(_X) 形式)  : %d' % len(zh_mn))
    print('  含行内 _X / &X 标记的词条     : %d%s' % (
        len(en_mn_inline), '' if not en_mn_inline else '（译文建议写成 译文(_X) 形式）'))
    for k in en_mn_inline[:5]:
        print('      %s = %r' % (k, a['entries'][k]))
    return 0


if __name__ == '__main__':
    sys.exit(main())

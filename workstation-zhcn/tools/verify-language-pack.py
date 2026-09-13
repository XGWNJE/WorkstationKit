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

    对比参照包时注意版本：若两者来自不同版本，会出现少量差异（新增/改写的词条、
    增删的占位符），属版本差异而非语言包缺陷。例如拿 17.6.4 的中文包与 26H1 的
    日语包对比，实测有个位数条目的占位符数量不同。
    要判断语言包自身有没有问题，看「格式异常行」与「占位符编号不连续」两项。
"""

import collections
import io
import os
import re
import sys

LINE_RE = re.compile(r'^[A-Za-z0-9_.\-]+ = ".*"$')
MNEMONIC_EN = re.compile(r'[_&]([A-Za-z0-9])')
MNEMONIC_ZH = re.compile(r'[(（][_&]([A-Za-z0-9])[)）]')
PH_ANY = re.compile(r'%(?:(\d+)\$)?([^\s%]*)')


def placeholders(value):
    """取出占位符，返回 [(索引或 None, 转换说明), ...]。

    兼容实际出现的各种写法，不要只认 %s/%d：
        printf 式   %s %d %u %x %I64d
        位置式      %1$s %2$u
        带修饰      %1$|23x
        字面量百分号 %%  （先剔除，不计入）
    """
    return PH_ANY.findall(value.replace('%%', ''))


def ph_count(value):
    return len(placeholders(value))


def bad_index(key, value):
    """位置式占位符的编号应从 1 开始且连续；不连续时回报。"""
    nums = sorted({int(n) for n, _ in placeholders(value) if n})
    if nums and nums != list(range(1, len(nums) + 1)):
        return ['%s = %r  编号 %s，期望 1..%d' % (key, value, nums, len(nums))]
    return []


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
            idx_bad = []
            for k in sorted(inter):
                n_ref = ph_count(b['entries'][k])
                n_tgt = ph_count(a['entries'][k])
                if n_ref != n_tgt:
                    mismatch.append((k, n_ref, n_tgt))
                idx_bad.extend(bad_index(k, a['entries'][k]))
            print('  占位符数量不匹配: %d %s' % (len(mismatch), '✓' if not mismatch else ''))
            for k, n_ref, n_tgt in mismatch[:8]:
                print('      %s: 参照=%d 本包=%d' % (k, n_ref, n_tgt))
            print('  占位符编号不连续: %d %s' % (len(idx_bad), '✓' if not idx_bad else ''))
            for s in idx_bad[:5]:
                print('      %s' % s)
            printf_left = [k for k, v in a['entries'].items()
                           if any(n is None for n, _ in placeholders(v))]
            print('  仍为 printf 式(未转位置式)的词条: %d%s' % (
                len(printf_left), '' if not printf_left else '（多为未翻译条目，会原样显示）'))

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

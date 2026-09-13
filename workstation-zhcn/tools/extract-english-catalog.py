#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 VMware Workstation 安装目录的二进制中提取英文界面词条。

英文原文并不以文本文件形式存在，而是以 "hashdata" 表内嵌在二进制里，格式为：

    @&!*@*@(键)英文值\\0

本脚本扫描安装目录下的可执行文件与 DLL，抽出 `键 = "英文值"` 列表，
输出的格式与 `messages/<locale>/vmware.vmsg` 完全一致，可直接作为翻译底稿。

用法:
    python extract-english-catalog.py <Workstation安装目录> [输出文件]

示例:
    python extract-english-catalog.py "C:\\Program Files\\VMware\\VMware Workstation" en-catalog.txt

说明:
    - 只读取文件，不修改任何东西。
    - 同键以首个命中的文件为准。
    - 含换行的值会被跳过（此类值不适合放进 .vmsg 的单行格式）。
"""

import collections
import glob
import io
import os
import re
import sys

MARK = b'@&!*@*@'
KEYMAX = 120
VALMAX = 4000


def candidates(root):
    pats = ['*.dll', '*.exe',
            os.path.join('x64', '*.exe'),
            os.path.join('x64', '*.dll')]
    files = []
    for p in pats:
        files.extend(glob.glob(os.path.join(root, p)))
    return sorted(set(files))


def extract(root):
    entries = {}          # key -> value
    order = []            # 保持首次出现顺序
    per_file = collections.Counter()

    for path in candidates(root):
        try:
            data = open(path, 'rb').read()
        except OSError:
            continue
        if MARK not in data:
            continue
        found = 0
        for m in re.finditer(re.escape(MARK), data):
            off = m.start() + len(MARK)
            if off >= len(data) or data[off:off + 1] != b'(':
                continue
            end = data.find(b')', off, off + KEYMAX + 1)
            if end < 0:
                continue
            key = data[off + 1:end].decode('ascii', 'replace')
            if not key or ' ' in key:
                continue
            val_end = data.find(b'\x00', end + 1, end + 1 + VALMAX)
            if val_end < 0:
                continue
            try:
                val = data[end + 1:val_end].decode('utf-8')
            except UnicodeDecodeError:
                continue
            if not val or '\r' in val or '\n' in val:
                continue
            if key not in entries:
                entries[key] = val
                order.append(key)
                found += 1
        if found:
            per_file[os.path.relpath(path, root)] = found

    return entries, order, per_file


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else 'en-catalog.txt'
    if not os.path.isdir(root):
        print('目录不存在: %s' % root)
        return 1

    entries, order, per_file = extract(root)
    if not entries:
        print('未提取到任何词条。请确认路径指向 Workstation 安装目录。')
        return 1

    print('各文件新增词条数:')
    for f, n in per_file.most_common():
        print('  %-34s %d' % (f, n))
    print()
    print('唯一词条总数: %d' % len(entries))
    pref = collections.Counter(k.split('.')[0] + '.' for k in order)
    print('前缀分布: %s' % ', '.join('%s=%d' % (p, n) for p, n in pref.most_common()))

    with io.open(out, 'w', encoding='utf-8', newline='\r\n') as fh:
        for k in order:
            v = entries[k].replace('"', '\\"')
            fh.write('%s = "%s"\n' % (k, v))
    print('已写出: %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())

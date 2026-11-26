"""把 km.ko 的 __versions 段里的 CRC 换成设备内核的真实值。

背景：这台平板的运行内核与 /vendor/lib/modules/*.ko 里的 CRC 对不上
（厂商 ko module_layout = 0xaad0c453，运行内核 = 0x670752f0），
所以用 OSS 源码编出来的 ko 一定 "disagrees about version of symbol module_layout"；
而 CONFIG_MODULE_FORCE_LOAD 没开，去掉 __versions 又会静默 ENOEXEC。

这里按 km/device_crcs.tsv（从 boot_a 的 __kcrctab 里读出来的真值）就地改写
__versions 段的条目 CRC，段本身保留。
"""
import struct
import sys

ENT = 8 + 56  # struct modversion_info: unsigned long crc + char name[MODULE_NAME_LEN]


def load_crcs(path):
    crcs = {}
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('symbol\t'):
            continue
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        crcs[parts[0]] = int(parts[1], 16)
    return crcs


def main(ko_path, tsv_path):
    crcs = load_crcs(tsv_path)
    d = bytearray(open(ko_path, 'rb').read())
    e_shoff = struct.unpack_from('<Q', d, 0x28)[0]
    e_shentsize = struct.unpack_from('<H', d, 0x3a)[0]
    e_shnum = struct.unpack_from('<H', d, 0x3c)[0]
    e_shstrndx = struct.unpack_from('<H', d, 0x3e)[0]
    soff = e_shoff + e_shstrndx * e_shentsize
    stroff = struct.unpack_from('<Q', d, soff + 24)[0]
    strtab = bytes(d[stroff:stroff + struct.unpack_from('<Q', d, soff + 32)[0]])
    vers = None
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        nameoff = struct.unpack_from('<I', d, o)[0]
        nm = strtab[nameoff:strtab.index(b'\0', nameoff)]
        if nm == b'__versions':
            vers = o
            break
    if vers is None:
        print('ERROR: ko 里没有 __versions 段（不要再用 objcopy 删它了）', file=sys.stderr)
        return 1
    off = struct.unpack_from('<Q', d, vers + 24)[0]
    size = struct.unpack_from('<Q', d, vers + 32)[0]
    changed, missing = 0, []
    for i in range(0, size - ENT + 1, ENT):
        name = bytes(d[off + i + 8:off + i + ENT]).split(b'\0')[0].decode('utf-8', 'replace')
        if name in crcs:
            struct.pack_into('<Q', d, off + i, crcs[name])
            changed += 1
            print(f'  patched {name:28s} -> 0x{crcs[name]:08x}')
        else:
            missing.append(name)
    open(ko_path, 'wb').write(d)
    print(f'共改写 {changed} 条；未在 tsv 里、保持原值的符号 {len(missing)} 条')
    if missing:
        print('  ' + ', '.join(missing[:20]) + (' ...' if len(missing) > 20 else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'km/device_crcs.tsv'))

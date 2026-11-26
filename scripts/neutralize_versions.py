"""把 __versions 段里的条目全部清零（名字变空串、CRC 变 0），但保留段本身。

原理（kernel/module.c 4.19，check_version()）：
    if (versindex == 0) return try_to_force_load(...) == 0;   // FORCE_LOAD 没开 → ENOEXEC
    for (i = 0; i < num_versions; i++)
        if (strcmp(versions[i].name, symname) == 0) { 比较 CRC ... }
    /* Broken toolchain. Warn once, then let it go.. */
    pr_warn_once("%s: no symbol version for %s\n", ...);
    return 1;                      // ← 没有对应条目时直接放行

所以：只要 __versions 段存在（versindex != 0）但里面没有 module_layout / printk /
init_uts_ns 这些名字，内核就只会打一条 "no symbol version for ..."，然后放行。
不需要知道运行内核的真实 CRC。
"""
import struct
import sys

ENT = 8 + 56


def main(ko):
    d = bytearray(open(ko, 'rb').read())
    e_shoff = struct.unpack_from('<Q', d, 0x28)[0]
    e_shentsize = struct.unpack_from('<H', d, 0x3a)[0]
    e_shnum = struct.unpack_from('<H', d, 0x3c)[0]
    e_shstrndx = struct.unpack_from('<H', d, 0x3e)[0]
    soff = e_shoff + e_shstrndx * e_shentsize
    stroff = struct.unpack_from('<Q', d, soff + 24)[0]
    strtab = bytes(d[stroff:stroff + struct.unpack_from('<Q', d, soff + 32)[0]])
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        nameoff = struct.unpack_from('<I', d, o)[0]
        if strtab[nameoff:strtab.index(b'\0', nameoff)] != b'__versions':
            continue
        off = struct.unpack_from('<Q', d, o + 24)[0]
        size = struct.unpack_from('<Q', d, o + 32)[0]
        # 保险：只保留一条名字为空的哑条目，其余清零
        d[off:off + size] = b'\x00' * size
        if size == 0:
            print('WARN: __versions 段长度为 0，versindex 仍存在但 num_versions=0，同样会放行')
        open(ko, 'wb').write(d)
        print(f'__versions 已清零：{size} 字节 / {size // ENT} 条条目 → 全部置为无名条目')
        return 0
    print('ERROR: 找不到 __versions 段', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))

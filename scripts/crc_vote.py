import struct, sys, glob, os, collections

# 4.19 modversions entry: struct modversion_info { unsigned long crc; char name[MODULE_NAME_LEN]; }
# MODULE_NAME_LEN = 64 - sizeof(unsigned long) = 56
ENT = 8 + 56


def parse(path):
    d = open(path, 'rb').read()
    (e_shoff, e_shentsize, e_shnum, e_shstrndx) = (
        struct.unpack_from('<Q', d, 0x28)[0],
        struct.unpack_from('<H', d, 0x3a)[0],
        struct.unpack_from('<H', d, 0x3c)[0],
        struct.unpack_from('<H', d, 0x3e)[0],
    )
    secs = []
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        name, typ, flags, addr, off, size, link, info, align, entsize = struct.unpack_from('<IIQQQQIIQQ', d, o)
        secs.append((name, typ, flags, off, size))
    strtab = d[secs[e_shstrndx][3]:secs[e_shstrndx][3] + secs[e_shstrndx][4]]
    out = {}
    for (name, typ, flags, off, size) in secs:
        nm = strtab[name:strtab.index(b'\0', name)].decode('utf-8', 'replace')
        out[nm] = (off, size, flags, typ)
    vers = {}
    if '__versions' in out:
        off, size, flags, typ = out['__versions']
        blob = d[off:off + size]
        for i in range(0, len(blob) - ENT + 1, ENT):
            crc = struct.unpack_from('<Q', blob, i)[0]
            nm = blob[i + 8:i + ENT].split(b'\0')[0].decode('utf-8', 'replace')
            vers[nm] = crc
    return vers, out, d


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else r'D:\ai\km\out\vkos'
    files = sorted(glob.glob(os.path.join(root, '*.ko')))
    layout = collections.Counter()
    missing = 0
    for f in files:
        vers, _, _ = parse(f)
        crc = vers.get('module_layout')
        if crc is None:
            missing += 1
        else:
            layout[crc] += 1
        print(f"{os.path.basename(f):45s} entries={len(vers):4d} module_layout={crc if crc is None else hex(crc)}")
    print("\n--- module_layout 投票 ---")
    for crc, n in layout.most_common():
        print(f"  {hex(crc)}  x{n}")
    print(f"  (无 __versions / 无 module_layout 的 ko: {missing})")

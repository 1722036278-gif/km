import struct, sys

TEXT = 0xFFFFFFA4C3880000
FSTART = 0x1000
KS_GPL = 0xFFFFFFA4C6128920
CRC_GPL = 0xFFFFFFA4C613BAA8
CRC_NONGPL = 0xFFFFFFA4C6133630

path, base = sys.argv[1], int(sys.argv[2], 0)
buf = open(path, 'rb').read()
v2f = lambda v: FSTART + (v - TEXT)


def rd(v, n):
    o = v2f(v) - base
    return buf[o:o + n] if 0 <= o and o + n <= len(buf) else None


def cstr(v):
    b = rd(v, 64)
    return b.split(b'\0')[0].decode('utf-8', 'replace') if b else None


n = (0xFFFFFFA4C6141130 - CRC_GPL) // 4
print(f"GPL 表条目数 {n}, 前 12 条:")
for i in range(12):
    e = rd(KS_GPL + i * 12, 12)
    if not e:
        print(i, "超范围")
        continue
    vo, no, nso = struct.unpack('<iii', e)
    print(f"  [{i}] name={cstr((KS_GPL+i*12+4+no) & 0xFFFFFFFFFFFFFFFF)!r}")

print("\n定向查找:")
for want in ['kallsyms_on_each_symbol', 'kallsyms_lookup_name', 'kallsyms_show_value']:
    hits = []
    for i in range(n):
        e = rd(KS_GPL + i * 12, 12)
        if not e:
            break
        vo, no, nso = struct.unpack('<iii', e)
        nm = cstr((KS_GPL + i * 12 + 4 + no) & 0xFFFFFFFFFFFFFFFF)
        if nm == want:
            crc = struct.unpack('<I', rd(CRC_GPL + i * 4, 4))[0]
            hits.append((i, crc))
    print(f"  {want}: {hits if hits else '未导出'}")

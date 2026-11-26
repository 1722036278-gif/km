import struct, sys

TEXT = 0xFFFFFFA4C3880000
FSTART = 0x1000
KS_NONGPL = 0xFFFFFFA4C6118030
KS_GPL = 0xFFFFFFA4C6128920
CRC_NONGPL = 0xFFFFFFA4C6133630
CRC_GPL = 0xFFFFFFA4C613BAA8

path = sys.argv[1]
base = int(sys.argv[2], 0)
buf = open(path, 'rb').read()


def v2f(v):
    return FSTART + (v - TEXT)


def rd(v, n):
    off = v2f(v) - base
    if off < 0 or off + n > len(buf):
        return None
    return buf[off:off + n]


def cstr(v, maxlen=64):
    b = rd(v, maxlen)
    if not b:
        return None
    return b.split(b'\0')[0].decode('utf-8', 'replace')


wanted = sys.argv[3].split(',') if len(sys.argv) > 3 else [
    'module_layout', 'printk', 'init_uts_ns', 'kallsyms_lookup_name']
found = {}

for (tabname, tab, crcbase, crcend) in [
        ('nongpl', KS_NONGPL, CRC_NONGPL, 0xFFFFFFA4C613BAA8),
        ('gpl', KS_GPL, CRC_GPL, 0xFFFFFFA4C6141130)]:
    n = (crcend - crcbase) // 4
    for i in range(n):
        e = rd(tab + i * 12, 12)
        if not e:
            continue
        vo, no, nso = struct.unpack('<iii', e)
        nm = cstr((tab + i * 12 + 4 + no) & 0xFFFFFFFFFFFFFFFF)
        if nm in wanted and nm not in found:
            crc = rd(crcbase + i * 4, 4)
            found[nm] = (struct.unpack('<I', crc)[0] if crc else None, tabname, i)

for w in wanted:
    if w in found:
        crc, tab, i = found[w]
        print(f"{w:24s} {tab:6s} idx={i:6d} crc=0x{crc:08x}")
    else:
        print(f"{w:24s} 未找到（可能未导出）")

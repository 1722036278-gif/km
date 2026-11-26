import struct, sys

TEXT_VADDR = 0xFFFFFFA4C3880000
FILE_KERNEL_START = 0x1000
KSYMTAB_MODULE_LAYOUT = 0xFFFFFFA4C6121048
MODULE_LAYOUT_FN = 0xFFFFFFA4C39971C0
MODULE_LAYOUT_NAME = 0xFFFFFFA4C6145A91

BASE = int(sys.argv[2], 0) if len(sys.argv) > 2 else 42660000
buf = open(sys.argv[1], 'rb').read()


def v2f(v):
    return FILE_KERNEL_START + (v - TEXT_VADDR)


def read_at(v, n):
    off = v2f(v) - BASE
    if off < 0 or off + n > len(buf):
        print(f"  (vaddr 0x{v:x} → file 0x{v2f(v):x} 不在缓冲区内, off={off})")
        return None
    return buf[off:off + n]


print(f"buffer covers file 0x{BASE:x} .. 0x{BASE+len(buf):x}")
e = read_at(KSYMTAB_MODULE_LAYOUT, 12)
if e:
    vo, no, nso = struct.unpack('<iii', e)
    val = (KSYMTAB_MODULE_LAYOUT + vo) & 0xFFFFFFFFFFFFFFFF
    nmv = (KSYMTAB_MODULE_LAYOUT + 4 + no) & 0xFFFFFFFFFFFFFFFF
    print(f"entry: value_off={vo} name_off={no} ns_off={nso}")
    print(f"  value = 0x{val:x}  (期望 0x{MODULE_LAYOUT_FN:x})  {'✅' if val == MODULE_LAYOUT_FN else '❌'}")
    print(f"  name  = 0x{nmv:x}  (期望 0x{MODULE_LAYOUT_NAME:x})  {'✅' if nmv == MODULE_LAYOUT_NAME else '❌'}")
    s = read_at(nmv, 20)
    print(f"  name  字符串 = {s!r}")

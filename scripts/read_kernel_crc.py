import struct, sys

BASE = 42684000            # kmreg.bin 在 boot_a 里的起始偏移
TEXT_VADDR = 0xFFFFFFA4C3880000
FILE_KERNEL_START = 0x1000

KSYMTAB_MODULE_LAYOUT = 0xFFFFFFA4C6121048
START_KSYMTAB = 0xFFFFFFA4C6118030
START_KCRCTAB = 0xFFFFFFA4C6133630
MODULE_LAYOUT_FN = 0xFFFFFFA4C39971C0
MODULE_LAYOUT_NAME = 0xFFFFFFA4C6145A91

buf = open(sys.argv[1] if len(sys.argv) > 1 else r'D:\ai\km\out\kmreg.bin', 'rb').read()


def v2f(vaddr):
    return FILE_KERNEL_START + (vaddr - TEXT_VADDR)


def read_at(vaddr, n):
    off = v2f(vaddr) - BASE
    if off < 0 or off + n > len(buf):
        return None
    return buf[off:off + n]


idx = (KSYMTAB_MODULE_LAYOUT - START_KSYMTAB)
print(f"ksymtab 区偏移 = 0x{idx:x}, 若每项 12 字节 → index = {idx/12}")
index = idx // 12
entry = read_at(KSYMTAB_MODULE_LAYOUT, 12)
if entry:
    vo, no, nso = struct.unpack('<iii', entry)
    print(f"ksymtab entry: value_off={vo} name_off={no} ns_off={nso}")
    print(f"  → 解出 value  = 0x{(KSYMTAB_MODULE_LAYOUT + vo) & 0xffffffffffffffff:x}  (期望 0x{MODULE_LAYOUT_FN:x})")
    name_v = KSYMTAB_MODULE_LAYOUT + 4 + no
    print(f"  → 解出 name   = 0x{name_v & 0xffffffffffffffff:x}  (期望 0x{MODULE_LAYOUT_NAME:x})")
    nm = read_at(name_v, 16)
    print(f"  → name 字符串 = {nm!r}")

crc_v = START_KCRCTAB + index * 4
raw = read_at(crc_v, 8)
print(f"\n__kcrctab[{index}] vaddr=0x{crc_v:x}  file=0x{v2f(crc_v):x}")
if raw:
    vals = struct.unpack('<II', raw)
    print("  8 字节:", " ".join(hex(v) for v in vals))
    print(f"  → module_layout CRC 候选 = 0x{vals[0]:08x}   （厂商 ko 里是 0xaad0c453）")

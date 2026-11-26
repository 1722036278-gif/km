import struct, sys

p = sys.argv[1] if len(sys.argv) > 1 else r"D:\ai\km\out\x\km\hide_ksu_mnt.ko"
d = open(p, 'rb').read()
ei = d[:16]
print("magic:", ei[:4] == b'\x7fELF', "class:", ei[4], "(2=64bit)", "data:", ei[5], "(1=LSB)", "osabi:", ei[6])
(e_type, e_machine, e_version, e_entry, e_phoff, e_shoff, e_flags, e_ehsize,
 e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx) = struct.unpack_from('<HHIQQQIHHHHHH', d, 16)
print(f"e_type={e_type} (1=REL)  e_machine={e_machine} (183=aarch64)  shnum={e_shnum}  phnum={e_phnum}  flags=0x{e_flags:x}")

secs = []
for i in range(e_shnum):
    o = e_shoff + i * e_shentsize
    name, typ, flags, addr, off, size, link, info, align, entsize = struct.unpack_from('<IIQQQQIIQQ', d, o)
    secs.append([name, typ, flags, off, size])

shstr = secs[e_shstrndx]
strtab = d[shstr[3]:shstr[3] + shstr[4]]
names = []
for s in secs:
    off = s[0]
    end = strtab.index(b'\0', off)
    nm = strtab[off:end].decode('utf-8', 'replace')
    names.append(nm)
    print(f"  {nm:22s} type={s[1]:2d} flags=0x{s[2]:x} size={s[4]}")

modinfo = b''
for nm, s in zip(names, secs):
    if nm == '.modinfo':
        modinfo = d[s[3]:s[3] + s[4]]
print("--- .modinfo ---")
for item in modinfo.split(b'\0'):
    if item:
        print("  " + item.decode('utf-8','replace'))

#!/usr/bin/env python3
"""校验 Module.symvers 里 module_layout 的 CRC 是否等于设备内核的期望值。

设备侧证据：/vendor/lib/modules/lcd.ko 的 __versions 段
    module_layout  0xaad0c453
（vermagic: 4.19.157-perf-gf8cf95f4dc15 SMP preempt mod_unload modversions aarch64）

用法:
    check_crc.py <Module.symvers> [期望CRC]
退出码:
    0 = 匹配（可以继续编 km.ko 并直接 insmod）
    1 = 不匹配（这个分支/配置的源码和设备内核不是同一份，换分支）
    2 = 文件里找不到 module_layout
"""
import sys

EXPECTED_DEFAULT = 0xAAD0C453


def parse_symvers(path):
    """返回 {symbol: crc}，兼容 4.19 的 tab 分隔格式。"""
    out = {}
    # utf-8-sig：容忍 Windows 编辑器/CI 意外写入的 BOM
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            try:
                crc = int(parts[0], 16)
            except ValueError:
                continue
            out[parts[1]] = crc
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    expected = int(sys.argv[2], 0) if len(sys.argv) > 2 else EXPECTED_DEFAULT

    syms = parse_symvers(path)
    got = syms.get("module_layout")
    if got is None:
        print(f"MISSING  module_layout 不在 {path} 里（可能 vmlinux 没编完）")
        return 2

    if got == expected:
        print(f"MATCH    module_layout = 0x{got:08x}  (expected 0x{expected:08x})")
        return 0

    print(f"MISMATCH module_layout = 0x{got:08x}  (expected 0x{expected:08x})")
    return 1


if __name__ == "__main__":
    sys.exit(main())

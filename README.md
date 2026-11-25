# km — elish 内核模块（抹掉 app mount namespace 里的 KSU 痕迹）

设备：小米平板 5 Pro（elish / sm8250），HyperOS 1.0.2.0（Android 13）
内核：`4.19.157-perf-gf8cf95f4dc15`，clang 14.0.7 (r450784d)，`CONFIG_MODVERSIONS=y`

## 为什么要 CI

`CONFIG_MODVERSIONS=y` 意味着模块里每个导入符号都带 CRC，且必须和本机内核一致；
`module_layout` 的期望值已经从设备 `/vendor/lib/modules/lcd.ko` 的 `__versions` 段
读出来了：

```
module_layout  0xaad0c453
```

这个值只有在「同一份源码 + 同一份 .config」下重编内核才会一致，本机没有 WSL/docker，
所以在 GitHub Actions 里编：

1. `discover` 先把 MiCode/Xiaomi_Kernel_OpenSource 里所有 `elish`/`sm8250` 分支列出来；
2. `build` 矩阵逐个：浅克隆 → 套 `config/device.config` → 编 `vmlinux` → 校验
   `module_layout == 0xaad0c453` → 对得上的才继续 `make M=km modules` → 产出
   `hide_ksu_mnt.ko` + `Module.symvers`；
3. vermagic 用 `CONFIG_LOCALVERSION="-perf"` + `LOCALVERSION="-gf8cf95f4dc15"` 精确重建，
   编完再断言一次字符串等于 `4.19.157-perf-gf8cf95f4dc15 SMP preempt mod_unload modversions aarch64`。

跑一次大概 8 个分支 × 40 分钟（并行），先对上的那个分支就是设备内核的源码。

## 目录

```
config/device.config      设备 /proc/config.gz 导出（6332 行）
km/hide_ksu_mnt.c         模块源码（v1 探针版：解析符号并打印，验证加载链路）
km/Kbuild                 模块编译规则
scripts/check_crc.py      校验 Module.symvers 的 module_layout
.github/workflows/build-km.yml
```

## 本地验证

```bash
python3 scripts/check_crc.py /path/to/Module.symvers 0xaad0c453
```

## 拿到 km.ko 之后

```sh
adb push hide_ksu_mnt.ko /data/local/tmp/
adb shell su -c 'insmod /data/local/tmp/hide_ksu_mnt.ko'
adb shell su -c 'dmesg | grep hide_ksu_mnt'
```

dmesg 里能看到 `hide_ksu_mnt: ready, N/7 symbols resolved` 就说明加载链路通了，
下一步再把 `do_new_mount` / `vfs_statx` 的 inline hook 加进去（v2）：

- `do_new_mount`：caller 不是 init ns 时，`name == "KSU"` 直接返回 `-ENOENT`
  → app 进程 exec 时 KSU 再也挂不上 `/debug_ramdisk`，省掉每 10s 一次的 nsenter+umount；
- `vfs_statx`：app uid（>=10000）stat `/data/adb`、`/system/bin/su` 返回 `-ENOENT`；
- `/proc/modules`、`/proc/self/mountinfo` 过滤：模块自己保持不可见。

加载带看门狗防 panic 循环：`post-fs-data.sh` 先写 `$STATE_DIR/km_pending` 再 insmod，
`boot_completed` 后删标记；下次开机发现标记还在就跳过 insmod。

# km 编译进度（交接笔记）

更新时间：2026-11-25 22:41

## 目标
在 CI 里用设备 config 复刻原厂 CRC，编出能被 elish 直接 `insmod` 的 `hide_ksu_mnt.ko`。
判定标准：`Module.symvers` 里 `module_layout == 0xaad0c453` 且 vermagic == `4.19.157-perf-gf8cf95f4dc15 SMP preempt mod_unload modversions aarch64`。

## 仓库 / 凭据
- 仓库：https://github.com/1722036278-gif/km （owner `1722036278-gif`）
- PAT：`D:\ai\gh_token.txt`（classic token，scope `repo,workflow`；用完可在设置里删）
- 本机 git 走 `socks5h://127.0.0.1:10808`（v2rayN socks，无 http 端口）
- 远程 GitHub 已开启 Actions：`ubuntu-22.04` / `aarch64-linux-gnu-gcc 11.4` / `ld 2.38`

## 已修（8 轮 CI）
| run | 报错 | 修法 |
|---|---|---|
| 45627149259 | ubuntu-26.04 没 clang-14 | 钉 `ubuntu-22.04` |
| 45628704524 | `CC_NAME` 只在 GITHUB_ENV、当前 shell 未赋值 | 当前 shell 先赋值 |
| 45629212186 | `OUT: unbound variable` | `echo OUT=$OUT >> $GITHUB_ENV` |
| 45630064716 | `empty.o` 汇编失败 + dtc `yylloc` 多重定义 | 换 gcc 交叉编译 + `HOSTCFLAGS=-fcommon` |
| 45630637022 / 45631452465 | `-Werror=implicit-int`、`-Werror=strict-prototypes`（小米 smp.c / power_debug.c） | `KCFLAGS` 降级为 warning |
| 45632410982 | `always_inline 'is_top_app' body not available`（sched.h `extern inline` + core.c `inline`） | sed 改成普通外部函数 |
| 45634227723 | `bq2597x_charger.c: -mgeneral-regs-only incompatible with floating-point` | 该行改整数占位 |

以上补丁均不影响 CRC（genksyms 只对类型签名做哈希）。

## 当前卡点（run 45634227723，2026-11-25 22:39 失败）
全部对象已编完（700s 到达 vmlinux 链接），链接阶段失败：

```
drivers/platform/msm/gsi/gsi.o:(__verbose+0x748): dangerous relocation: unsupported relocation
... (数十条，全部集中在 gsi.o 的 __verbose 段)
make[1]: *** [Makefile:1177: vmlinux] Error 1
```

这是 4.19 老内核 + binutils 2.38 的已知组合问题（老 ld 容忍、新 ld 报 dangerous relocation）。
明天任选其一，成本都很低：
1. **改链接器**：`LD=ld.lld`（装 `lld` 包）——lld 对这类 relocation 宽容，最省事；
2. **关掉该驱动**：`scripts/config -d CONFIG_MSM_GCI ...`（`drivers/platform/msm/gsi` 对应符号，需在 Kconfig 里确认；关驱动不影响 module_layout/我们需要的那几个 CRC）；
3. 给 `gsi.c` 的 `__verbose` 用法打补丁（把该段变量改成普通 `static`）。

## 下一步（明天照这个跑）
1. 按上面任一方案改 `.github/workflows/build-km.yml` 的 `修补厂商源码` / `编 vmlinux` 步骤 → push → 等 `编 vmlinux` 通过；
2. `校验 module_layout CRC` 步骤出结论：`0xaad0c453` 对上就是这份源码；对不上则换 discover 列出的其他 elish 分支（或按提交日期对齐 `V816.0.2.0.TKYCNXM`）；
3. CRC 对上后：`make M=km modules` → 得到 `km/hide_ksu_mnt.ko` + `Module.symvers`；
4. 校验 vermagic 字符串完全一致；
5. 下载 artifact 到 `D:\ai\km\out\`，**先在设备上 `insmod` 只打印 pr_info 的探针版**（`dmesg | grep hide_ksu_mnt` 看 7 个符号地址是否解析成功），成功后再写 hook 逻辑；
6. 用户 m01406 要求：**验证成功之后才安装**（不要在未验证的情况下塞进模块目录/开机加载）。

## 设备侧当前状态（未被本次 CI 影响）
- 模块 `sukisu_tencent_hide` v2.1.1 已装并运行，`ACE_GUARD=0`、`ACE_GUARD_TMP=0`、`MNT_SANITIZE=1`、`MGR_HIDE=0`；
- 守护 `game_boost.sh --fg` 在跑（开局 90s 内做 mnt 清洗，之后不再打扰）；
- ace_check 上次 29 PASS / 1 FAIL（包可见性，靠 `play_ready.sh off` 手动收）；
- 桌面已恢复 SukiSU Ultra / MT 图标；`pm hide` 只用 `mgr_toggle.sh`。

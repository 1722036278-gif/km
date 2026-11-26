// SPDX-License-Identifier: GPL-2.0
/*
 * hide_ksu_mnt —— 探针版 v3（只验证加载链路，不做任何 hook）
 *
 * 目标设备：Xiaomi elish (平板 5 Pro), 4.19.157-perf-gf8cf95f4dc15
 *
 * v2 用 kallsyms_lookup_name 自举，但实测该内核没有导出 kallsyms_lookup_name
 * （也没有 kallsyms_on_each_symbol / set_memory_rw / kprobes），所以 v3 改成
 * 只引用「确认已导出」的符号，用来证明三件事：
 *   1) 交叉编译出的 ko 能被这个内核接受（vermagic + __versions CRC 都对齐）
 *   2) init/exit 能执行（dmesg 有输出）
 *   3) 我们能拿到的内核句柄有哪些（决定后续 hook 方案）
 *
 * 作者：YG
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/utsname.h>
#include <linux/fs.h>
#include <linux/namei.h>

#define HKM_TAG "hide_ksu_mnt"

/* 只引用 100% 已导出、且头文件里就有声明的符号：
 *   printk      —— nongpl #3654, CRC 0x17b41e09
 *   init_uts_ns —— nongpl #7128, CRC 0x24428be5
 * vfs_statx 虽然导出（#5254），但这套 4.19 源码里它的原型和 4.19.157 出厂内核不一致，
 * 在模块里 extern 声明会 conflicting types，先不引用它。
 */

static int __init hkm_init(void)
{
	pr_info("%s: loaded, kernel release = %s\n", HKM_TAG, init_uts_ns.name.release);
	pr_info("%s: printk      @ %pS\n", HKM_TAG, (void *)printk);
	pr_info("%s: init_uts_ns @ %px\n", HKM_TAG, (void *)&init_uts_ns);
	pr_info("%s: probe ok (no hook)\n", HKM_TAG);
	return 0;
}

static void __exit hkm_exit(void)
{
	pr_info("%s: unloaded\n", HKM_TAG);
}

module_init(hkm_init);
module_exit(hkm_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("YG");
MODULE_DESCRIPTION("elish module-load probe v3 (verification only)");

// SPDX-License-Identifier: GPL-2.0
/*
 * hide_ksu_mnt —— 探针版 v2（只验证加载链路与符号可解析性，不做任何 hook）
 *
 * 目标设备：Xiaomi elish (平板 5 Pro), 4.19.157-perf-gf8cf95f4dc15
 * 加载后 dmesg 里应看到一行 "[hide_ksu_mnt] symbols:" 以及各符号地址；
 * 若某个符号打印 0，说明该内核没有导出它（要换方案）。
 *
 * 作者：YG
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/utsname.h>
#include <linux/kallsyms.h>

#define HKM_TAG "hide_ksu_mnt"

/* 内核 4.19 里 kallsyms_lookup_name 仍是导出符号（GPL） */
typedef unsigned long (*kln_t)(const char *name);

static kln_t kln;

static const char * const targets[] = {
	"kallsyms_lookup_name",
	"do_new_mount",
	"vfs_kern_mount",
	"vfs_statx",
	"set_memory_rw",
	"set_memory_ro",
	"kern_path",
	"path_umount",
	"iterate_mounts",
	"kern_mount",
};

static int __init hkm_init(void)
{
	unsigned long a;
	int i;

	pr_info("%s: loading, release=%s\n", HKM_TAG, init_uts_ns.name.release);

	kln = (kln_t)kallsyms_lookup_name("kallsyms_lookup_name");
	if (!kln) {
		pr_err("%s: kallsyms_lookup_name 解析失败\n", HKM_TAG);
		return -ENOENT;
	}

	pr_info("%s: symbols:\n", HKM_TAG);
	for (i = 0; i < ARRAY_SIZE(targets); i++) {
		a = kln(targets[i]);
		pr_info("%s:   %-24s = 0x%lx%s\n", HKM_TAG, targets[i], a,
			a ? "" : "   <-- 未解析");
	}

	pr_info("%s: probe ok (无 hook，仅供验证)\n", HKM_TAG);
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
MODULE_DESCRIPTION("elish mount/symbol probe (verification only)");

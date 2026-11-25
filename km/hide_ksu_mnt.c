// SPDX-License-Identifier: GPL-2.0
/*
 * hide_ksu_mnt - 在内核里抹掉 KSU/SUSFS 在 app mount namespace 留下的痕迹
 *
 * 设计要点（基于 elish / 4.19.157 实测）：
 *   - 4.19 没有 kprobe（CONFIG_KPROBES 未开），只能 inline hook。
 *   - kptr_restrict=2，用户态拿不到地址，必须模块内部 kallsyms_lookup_name 解析。
 *   - 每个 app 进程 exec 时 KSU 都会重新挂一次 "KSU /debug_ramdisk"，用户态
 *     nsenter+umount 只能事后补救（每 10s 一次 373ms CPU），内核里拦才干净。
 *
 * v1（本文件）= 探针版：只解析并打印符号地址，验证「编出来的 ko 能否 insmod」。
 * 校验点：Module.symvers 里 module_layout 必须等于 0xaad0c453，
 *         否则 vermagic/CRC 不匹配，insmod 直接 ENOEXEC。
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kallsyms.h>
#include <linux/slab.h>
#include <linux/uaccess.h>

#define HKM_TAG "hide_ksu_mnt"

/* 需要解析的内核符号（v1 只解析，v2 拿去做 inline hook） */
static const char * const hkm_targets[] = {
	"kallsyms_lookup_name",
	"do_new_mount",
	"vfs_kern_mount",
	"vfs_statx",
	"set_memory_rw",
	"set_memory_ro",
	"kern_path",
};

#define HKM_NR_TARGETS ARRAY_SIZE(hkm_targets)

static unsigned long hkm_addr[HKM_NR_TARGETS];

static int __init hkm_init(void)
{
	unsigned int i, ok = 0;

	pr_info("%s: loading (vermagic=%s)\n", HKM_TAG, VERMAGIC_STRING);

	for (i = 0; i < HKM_NR_TARGETS; i++) {
		hkm_addr[i] = kallsyms_lookup_name(hkm_targets[i]);
		if (hkm_addr[i]) {
			ok++;
			pr_info("%s: %-22s = 0x%lx\n", HKM_TAG,
				hkm_targets[i], hkm_addr[i]);
		} else {
			pr_warn("%s: %-22s not found\n", HKM_TAG,
				hkm_targets[i]);
		}
	}

	pr_info("%s: ready, %u/%u symbols resolved\n",
		HKM_TAG, ok, (unsigned int)HKM_NR_TARGETS);
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
MODULE_DESCRIPTION("hide KSU/SUSFS traces in app mount namespaces");
MODULE_VERSION("0.1.0");

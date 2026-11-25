# 外部模块编译入口（CI 里用 make -C $KSRC M=$PWD/km modules，本文件仅在本地手动编译时使用）
KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	$(MAKE) -C $(KDIR) M=$(CURDIR) modules

clean:
	$(MAKE) -C $(KDIR) M=$(CURDIR) clean

.PHONY: all clean

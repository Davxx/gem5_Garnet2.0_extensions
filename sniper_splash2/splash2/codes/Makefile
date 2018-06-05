SPLASH_ROOT = /home/dav/gem5/sniper_splash2/splash2/codes

include /home/dav/gem5/sniper_splash2/tools/hooks/buildconf.makefile

CC = ${HOOKS_CC}
CXX = ${HOOKS_CXX}
LD ?= ${CC}
CFLAGS = -g -O3 -I${SPLASH_ROOT} -I/home/dav/gem5/m5threads -I/home/dav/gem5/util/m5/ ${HOOKS_CFLAGS}
LDFLAGS = -lm -pthread ${HOOKS_LDFLAGS}
MACROS = /home/dav/gem5/sniper_splash2/splash2/codes/pthreads/c.m4.null.POSIX

all:
	$(MAKE) -C /home/dav/gem5/sniper_splash2/tools/hooks
	for DIR in `find apps kernels -name \[Mm\]akefile|sed -e 's+/[Mm]akefile++'|sort -r`; do CC="$(CC)" AR="$(AR)" LD="$(LD)" CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)" MACROS="$(MACROS)" TARGET_ARCH="" $(MAKE) -C $$DIR all; if [ $$? -eq 0 ]; then echo; else exit -1; fi; done

clean:
	$(MAKE) -C /home/dav/gem5/sniper_splash2/tools/hooks clean
	for DIR in `find apps kernels -name \[Mm\]akefile|sed s+/[Mm]akefile++|sort -r`; do $(MAKE) -C $$DIR clean; done

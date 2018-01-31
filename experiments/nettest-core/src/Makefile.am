AUTOMAKE_OPTIONS = foreign

GIT_VERSION := $(shell git describe --abbrev=9 --dirty --always --tags --long 2> /dev/null)

WARNINGS =	-Wall -Wextra -Wformat=2 -Wswitch-default -Wcast-align -Wpointer-arith \
    -Wbad-function-cast -Wstrict-prototypes -Winline -Wundef -Wnested-externs \
    -Wcast-qual -Wshadow -Wwrite-strings -Wconversion -Wunreachable-code \
    -pedantic -Wdisabled-optimization -Winit-self -Wmissing-declarations -Wmissing-include-dirs \
    -Wmissing-prototypes -Wparentheses -Wredundant-decls -Wsequence-point \
    -Wsign-compare -Wuninitialized -Wno-format-nonliteral -Wmissing-noreturn
OPTS =		-fno-common -fstrict-aliasing -fmessage-length=0

AM_CFLAGS = -std=gnu11 -O3 -g $(WARNINGS) $(OPTS)

AM_CFLAGS += $(if $(GIT_VERSION),-DGIT_VERSION=\"$(GIT_VERSION)\",)

AM_LDFLAGS = -pthread

bin_PROGRAMS = rmbt
rmbt_SOURCES = rmbt.c \
    rmbt_common.h \
    rmbt_compress.c \
    rmbt_compress.h \
    rmbt_config.h \
    rmbt_flow.c \
    rmbt_flow.h \
    rmbt.h \
    rmbt_helper.c \
    rmbt_helper.h \
    rmbt_json.c \
    rmbt_json.h \
    rmbt_result.c \
    rmbt_result.h \
    rmbt_ssl.c \
    rmbt_ssl.h \
    rmbt_stats.c \
    rmbt_stats.h \
    rmbt_token.c \
    rmbt_token.h

rmbt_CFLAGS = $(JSON_CFLAGS) $(UUID_CFLAGS) $(SSL_CFLAGS) $(LZMA_CFLAGS) $(AM_CFLAGS)
rmbt_LDADD = $(JSON_LIBS) $(UUID_LIBS) $(SSL_LIBS) $(LZMA_LIBS)

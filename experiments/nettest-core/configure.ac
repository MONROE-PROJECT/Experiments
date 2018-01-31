#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.61])
AC_INIT(rmbt-client,
	m4_esyscmd_s([git describe --abbrev=9 --dirty --always --tags --long 2> /dev/null || echo unknown]),
	[https://github.com/lwimmer/rmbt-client/issues],,
	[https://github.com/lwimmer/rmbt-client])
AM_INIT_AUTOMAKE([foreign std-options -Wall -Werror -Wno-portability])
m4_ifdef([AM_SILENT_RULES], [AM_SILENT_RULES([yes])])
AC_CONFIG_SRCDIR([src/rmbt.c])
AC_CONFIG_HEADERS([config.h])

AC_USE_SYSTEM_EXTENSIONS

AC_PROG_CC([cc gcc clang])

# Checks for libraries.
PKG_CHECK_MODULES([UUID], [uuid], [AC_DEFINE([HAVE_UUID], [1], [Use libuuid])])
PKG_CHECK_MODULES([SSL], [libssl libcrypto], [AC_DEFINE([HAVE_LIBSSL], [1], [Use libssl])])
PKG_CHECK_MODULES([JSON], [json-c], [AC_DEFINE([HAVE_JSONC], [1], [Use json-c])])
PKG_CHECK_MODULES([LZMA], [liblzma], [AC_DEFINE([HAVE_LZMA], [1], [Use liblzma])], [true])

AC_CONFIG_FILES([Makefile src/Makefile])
AC_OUTPUT

#!/bin/sh
set -e
[ -e configure ] || autoreconf -i
[ -e Makefile ]  || ( ./configure && make )
[ -e src/rmbt ] || make

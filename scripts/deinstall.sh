#!/bin/bash

CMD='rm -r /usr/local/bin/mmgen-* /usr/local/lib/python2.7/dist-packages/mmgen*'

set -x

if [ "$EUID" = 0 ]; then $CMD; else sudo $CMD; fi

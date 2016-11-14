#!/bin/bash

CMD='rm -rf /usr/local/bin/mmgen-* /usr/local/lib/python2.7/dist-packages/mmgen*'

if [ "$EUID" = 0 ]; then
	set -x; $CMD
else
	set -x; sudo $CMD
fi

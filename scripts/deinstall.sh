#!/bin/bash

CMD='rm -rf /usr/local/share/mmgen /usr/local/bin/mmgen-* /usr/local/lib/python2.7/dist-packages/mmgen* /mingw/opt/bin/mmgen-* /mingw/opt/lib/python2.7/site-packages/mmgen*'

if [ "$EUID" = 0 -o "$HOMEPATH" ]; then
	set -x; $CMD
else
	set -x; sudo $CMD
fi

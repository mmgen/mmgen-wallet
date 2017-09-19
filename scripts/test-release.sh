#!/bin/bash
# Tested on Linux, MinGW-64

set -e
GREEN="\e[32;1m" YELLOW="\e[33;1m" RESET="\e[0m" BRANCH=$1
REFDIR=test/ref
if uname -a | grep -qi mingw; then SUDO='' MINGW=1; else SUDO='sudo' MINGW=''; fi

function check {
	[ "$BRANCH" ] || { echo 'No branch specified.  Exiting'; exit; }
	[ "$(git diff $BRANCH)" == "" ] || {
		echo "Unmerged changes from branch '$BRANCH'. Exiting"
		exit
	}
	git diff $BRANCH >/dev/null 2>&1 || exit
}

function install {
	set -x
	eval "$SUDO rm -rf .test-release"
	git clone --branch $BRANCH --single-branch . .test-release
	cd .test-release
	./setup.py sdist
	mkdir pydist && cd pydist
	if [ "$MINGW" ]; then unzip ../dist/mmgen-*.zip; else tar zxvf ../dist/mmgen-*gz; fi
	cd mmgen-*
	scripts/deinstall.sh

	[ "$MINGW" ] && ./setup.py build --compiler=mingw32
	eval "$SUDO ./setup.py install"
}

function do_test {
	set +x
	for i in "${CMDS[@]}"; do
		echo -e "\n${GREEN}Running:$RESET $YELLOW$i$RESET"
		eval "$i"
	done
}

check
(install)

eval "cd .test-release/pydist/mmgen-*"

CMDS=(
	'test/test.py -On'
	'test/test.py -On --segwit dfl_wallet main ref ref_other'
	'test/test.py -On --segwit-random dfl_wallet main'
)
do_test

CMDS=('test/test.py -On regtest')
do_test

# tooltest tests both segwit and non-segwit
CMDS=(
	'test/tooltest.py'
	"test/gentest.py -q 2 $REFDIR/btcwallet.dump"
	"test/gentest.py -q --testnet=1 2 $REFDIR/btcwallet-testnet.dump"
	'test/gentest.py -q 1:2 10'
	'test/gentest.py -q --segwit 1:2 10'
#	"scripts/tx-old2new.py -S $REFDIR/tx_*raw >/dev/null 2>&1"
	"scripts/compute-file-chksum.py $REFDIR/*testnet.rawtx >/dev/null 2>&1"
)
do_test

echo -e "\n${GREEN}All OK$RESET"

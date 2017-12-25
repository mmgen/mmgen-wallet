#!/bin/bash
# Tested on Linux, MinGW-64
# MinGW's bash 3.1.17 doesn't do ${var^^}

dfl_tests='obj misc_ni alts misc btc btc_tn btc_rt bch bch_rt ltc ltc_tn ltc_rt tool gen'
PROGNAME=$(basename $0)
while getopts hinPt OPT
do
	case "$OPT" in
	h)  printf "  %-16s Test MMGen release\n" "${PROGNAME}:"
		echo   "  USAGE:           $PROGNAME [options] branch [tests]"
		echo   "  OPTIONS: '-h'  Print this help message"
		echo   "           '-i'  Install only; don't run tests"
		echo   "           '-n'  Don't install; test in place"
		echo   "           '-P'  Don't pause between tests"
		echo   "           '-t'  Print the tests without running them"
		echo   "  AVAILABLE TESTS:"
		echo   "     obj     - data objects"
		echo   "     misc_ni - miscellaneous operations (non-interactive tests)"
		echo   "     alts    - operations for all supported gen-only altcoins"
		echo   "     misc    - miscellaneous operations (interactive tests)"
		echo   "     btc     - bitcoin"
		echo   "     btc_tn  - bitcoin testnet"
		echo   "     btc_rt  - bitcoin regtest"
		echo   "     bch     - bitcoin cash (BCH)"
		echo   "     bch_rt  - bitcoin cash (BCH) regtest"
# 		echo   "     b2x     - bitcoin 2x (B2X)"
# 		echo   "     b2x_rt  - bitcoin 2x (B2X) regtest"
		echo   "     ltc     - litecoin"
		echo   "     ltc_tn  - litecoin testnet"
		echo   "     ltc_rt  - litecoin regtest"
		echo   "     tool    - tooltest (all supported coins)"
		echo   "     gen     - gentest (all supported coins)"
		echo   "  By default, all tests are run"
		exit ;;
	i)  INSTALL_ONLY=1 ;;
	n)  NO_INSTALL=1 ;;
	P)  NO_PAUSE=1 ;;
	t)  TESTING=1 ;;
	*)  exit ;;
	esac
done

shift $((OPTIND-1))

RED="\e[31;1m" GREEN="\e[32;1m" YELLOW="\e[33;1m" RESET="\e[0m"

BRANCH=$1; shift
BRANCHES=$(git branch)
FOUND_BRANCH=$(for b in ${BRANCHES/\*}; do [ "$b" == "$BRANCH" ] && echo ok; done)
[ "$FOUND_BRANCH" ] || { echo "Branch '$BRANCH' not found!"; exit; }

set -e

REFDIR=test/ref
if uname -a | grep -qi mingw; then SUDO='' MINGW=1; else SUDO='sudo' MINGW=''; fi

check() {
	[ "$BRANCH" ] || { echo 'No branch specified.  Exiting'; exit; }
	[ "$(git diff $BRANCH)" == "" ] || {
		echo "Unmerged changes from branch '$BRANCH'. Exiting"
		exit
	}
	git diff $BRANCH >/dev/null 2>&1 || exit
}

install() {
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
do_test() {
	set +x
	for i in "$@"; do
		LS='\n'
		[ "$TESTING" ] && LS=''
		echo $i | grep -q 'gentest' && LS=''
		echo -e "$LS${GREEN}Running:$RESET $YELLOW$i$RESET"
		[ "$TESTING" ] || eval "$i" || { echo -e $RED'Test failed!'$RESET; exit; }
	done
}
i_obj='Data object'
s_obj='Testing data objects'
t_obj=(
    'test/objtest.py --coin=btc -S'
    'test/objtest.py --coin=btc --testnet=1 -S'
    'test/objtest.py --coin=ltc -S'
    'test/objtest.py --coin=ltc --testnet=1 -S')
f_obj='Data object test complete'

i_alts='Gen-only altcoin'
s_alts='The following tests will test generation operations for all supported altcoins'
ROUNDS=100
ROUNDS_LOW=20
ROUNDS_SPEC=500
t_alts=(
	'test/scrambletest.py'
	'test/test.py -n altcoin_ref'
	"test/gentest.py --coin=btc 2 $ROUNDS"
	"test/gentest.py --coin=btc --type=compressed 2 $ROUNDS"
	"test/gentest.py --coin=btc --type=segwit 2 $ROUNDS"
	"test/gentest.py --coin=ltc 2 $ROUNDS"
	"test/gentest.py --coin=ltc --type=compressed 2 $ROUNDS"
	"test/gentest.py --coin=ltc --type=segwit 2 $ROUNDS"
	"test/gentest.py --coin=zec 2 $ROUNDS"
	"test/gentest.py --coin=etc 2 $ROUNDS"
	"test/gentest.py --coin=eth 2 $ROUNDS"
	"test/gentest.py --coin=zec --type=zcash_z 2 $ROUNDS_SPEC"

	"test/gentest.py --coin=btc 2:ext $ROUNDS"
	"test/gentest.py --coin=btc --type=compressed 2:ext $ROUNDS"
	"test/gentest.py --coin=btc --type=segwit 2:ext $ROUNDS"
	"test/gentest.py --coin=ltc 2:ext $ROUNDS"
	"test/gentest.py --coin=ltc --type=compressed 2:ext $ROUNDS"
#	"test/gentest.py --coin=ltc --type=segwit 2:ext $ROUNDS" # pycoin generates old-style LTC Segwit addrs
	"test/gentest.py --coin=etc 2:ext $ROUNDS"
	"test/gentest.py --coin=eth 2:ext $ROUNDS"
	"test/gentest.py --coin=zec 2:ext $ROUNDS"
	"test/gentest.py --coin=zec --type=zcash_z 2:ext $ROUNDS_SPEC"

	"test/gentest.py --all 2:pycoin $ROUNDS_LOW"
	"test/gentest.py --all 2:pyethereum $ROUNDS_LOW"
	"test/gentest.py --all 2:keyconv $ROUNDS_LOW"
	"test/gentest.py --all 2:zcash_mini $ROUNDS_LOW")

f_alts='Gen-only altcoin tests completed'

i_misc_ni='Miscellaneous operations (non-interactive)'
s_misc_ni='Testing miscellaneous operations (non-interactive)'
t_misc_ni=(
    'test/sha256test.py')
f_misc_ni='Miscellaneous non-interactive tests complete'

i_misc='Miscellaneous operations (interactive)' # includes autosign!
s_misc='The bitcoin, bitcoin-abc and litecoin (mainnet) daemons must be running for the following tests'
t_misc=(
    'test/test.py -On misc')
f_misc='Miscellaneous interactive tests test complete'

i_btc='Bitcoin mainnet'
s_btc='The bitcoin (mainnet) daemon must both be running for the following tests'
t_btc=(
    'test/test.py -On'
	'test/test.py -On --segwit dfl_wallet main ref ref_other'
	'test/test.py -On --segwit-random dfl_wallet main'
    'test/tooltest.py rpc'
	"scripts/compute-file-chksum.py $REFDIR/*testnet.rawtx >/dev/null 2>&1")
f_btc='You may stop the bitcoin (mainnet) daemon if you wish'

i_btc_tn='Bitcoin testnet'
s_btc_tn='The bitcoin testnet daemon must both be running for the following tests'
t_btc_tn=(
    'test/test.py -On --testnet=1'
	'test/test.py -On --testnet=1 --segwit dfl_wallet main ref ref_other'
	'test/test.py -On --testnet=1 --segwit-random dfl_wallet main'
	'test/tooltest.py --testnet=1 rpc')
f_btc_tn='You may stop the bitcoin testnet daemon if you wish'

i_btc_rt='Bitcoin regtest'
s_btc_rt="The following tests will test MMGen's regtest (Bob and Alice) mode"
t_btc_rt=(
	'test/test.py -On regtest'
#	'test/test.py -On regtest_split' # no official B2X support, so skip
	)
f_btc_rt='Regtest (Bob and Alice) mode tests for BTC completed'

i_bch='Bitcoin cash (BCH)'
s_bch='The bitcoin cash daemon (Bitcoin ABC) must both be running for the following tests'
t_bch=('test/test.py -On --coin=bch dfl_wallet main ref ref_other')
f_bch='You may stop the Bitcoin ABC daemon if you wish'

i_bch_rt='Bitcoin cash (BCH) regtest'
s_bch_rt="The following tests will test MMGen's regtest (Bob and Alice) mode"
t_bch_rt=('test/test.py --coin=bch -On regtest')
f_bch_rt='Regtest (Bob and Alice) mode tests for BCH completed'

i_b2x='Bitcoin 2X (B2X)'
s_b2x='The bitcoin 2X daemon (BTC1) must both be running for the following tests'
t_b2x=('test/test.py -On --coin=b2x dfl_wallet main ref ref_other')
f_b2x='You may stop the Bitcoin 2X daemon if you wish'

i_b2x_rt='Bitcoin 2X (B2X) regtest'
s_b2x_rt="The following tests will test MMGen's regtest (Bob and Alice) mode"
t_b2x_rt=('test/test.py --coin=b2x -On regtest')
f_b2x_rt='Regtest (Bob and Alice) mode tests for B2X completed'

i_ltc='Litecoin'
s_ltc='The litecoin daemon must both be running for the following tests'
t_ltc=(
    'test/test.py --coin=ltc -On dfl_wallet main'
    'test/test.py --coin=ltc --segwit -On dfl_wallet main'
    'test/test.py --coin=ltc --segwit-random -On dfl_wallet main'
    'test/tooltest.py --coin=ltc rpc'
)
f_ltc='You may stop the litecoin daemon if you wish'

i_ltc_tn='Litecoin testnet'
s_ltc_tn='The litecoin testnet daemon must both be running for the following tests'
t_ltc_tn=(
    'test/test.py --coin=ltc -On --testnet=1'
	'test/test.py --coin=ltc -On --testnet=1 --segwit dfl_wallet main ref ref_other'
	'test/test.py --coin=ltc -On --testnet=1 --segwit-random dfl_wallet main'
	'test/tooltest.py --coin=ltc --testnet=1 rpc')
f_ltc_tn='You may stop the litecoin testnet daemon if you wish'

i_ltc_rt='Litecoin regtest'
s_ltc_rt="The following tests will test MMGen's regtest (Bob and Alice) mode"
t_ltc_rt=('test/test.py --coin=ltc -On regtest')
f_ltc_rt='Regtest (Bob and Alice) mode tests for LTC completed'

i_tool='Tooltest'
s_tool='The following tests will run test/tooltest.py for all supported coins'
t_tool=(
	'test/tooltest.py --coin=btc util'
	'test/tooltest.py --coin=btc cryptocoin'
	'test/tooltest.py --coin=btc mnemonic'
	'test/tooltest.py --coin=ltc cryptocoin'
	'test/tooltest.py --coin=eth cryptocoin'
	'test/tooltest.py --coin=etc cryptocoin'
	'test/tooltest.py --coin=dash cryptocoin'
	'test/tooltest.py --coin=doge cryptocoin'
	'test/tooltest.py --coin=emc cryptocoin'
	'test/tooltest.py --coin=zec cryptocoin'
	'test/tooltest.py --coin=zec --type=zcash_z cryptocoin')
f_tool='tooltest tests completed'

i_gen='Gentest'
s_gen='The following tests will run test/gentest.py on mainnet and testnet for all supported coins'
t_gen=(
	"test/gentest.py -q 2 $REFDIR/btcwallet.dump"
	'test/gentest.py -q 1:2 10'
	'test/gentest.py -q --type=segwit 1:2 10'
    "test/gentest.py -q --testnet=1 2 $REFDIR/btcwallet-testnet.dump"
	'test/gentest.py -q --testnet=1 1:2 10'
	'test/gentest.py -q --testnet=1 --type=segwit 1:2 10'
    "test/gentest.py -q --coin=ltc 2 $REFDIR/litecoin/ltcwallet.dump"
	'test/gentest.py -q --coin=ltc 1:2 10'
	'test/gentest.py -q --coin=ltc --type=segwit 1:2 10'
    "test/gentest.py -q --coin=ltc --testnet=1 2 $REFDIR/litecoin/ltcwallet-testnet.dump"
	'test/gentest.py -q --coin=ltc --testnet=1 1:2 10'
	'test/gentest.py -q --coin=ltc --testnet=1 --type=segwit 1:2 10'
	)
f_gen='gentest tests completed'

[ -d .git -a -z "$NO_INSTALL"  -a -z "$TESTING" ] && {
	check
	(install)
	eval "cd .test-release/pydist/mmgen-*"
}
[ "$INSTALL_ONLY" ] && exit

skip_maybe() {
    echo -n "Enter 's' to skip, or ENTER to continue: "; read
    [ "$REPLY" == 's' ] && return 0
    return 1
}

run_tests() {
	for t in $1; do
        eval echo -e \${GREEN}'###' Running $(echo \$i_$t) tests\$RESET
        [ "$PAUSE" ] && { eval echo $(echo \$s_$t); skip_maybe && continue; }
#       echo RUNNING
		eval "do_test \"\${t_$t[@]}\""
        eval echo -e \$GREEN$(echo \$f_$t)\$RESET
	done
}

check_args() {
	for i in $tests; do
		echo "$dfl_tests" | grep -q "\<$i\>" || { echo "$i: unrecognized argument"; exit; }
	done
}

tests=$dfl_tests
[ "$*" ] && tests="$*"
[ "$NO_PAUSE" ] || PAUSE=1

check_args
run_tests "$tests"

echo -e "${GREEN}All OK$RESET"

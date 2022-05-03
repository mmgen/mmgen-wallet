#!/bin/bash
# Tested on Linux, Armbian, Raspbian, MSYS2

REFDIR='test/ref'
SUDO='sudo'

if [ "$(uname -m)" == 'armv7l' ]; then
	ARM32=1
elif [ "$(uname -m)" == 'aarch64' ]; then
	ARM64=1
elif uname -a | grep -q 'MSYS'; then
	SUDO='' MSYS2=1;
fi

trap 'echo -e "${GREEN}Exiting at user request$RESET"; exit' INT

umask 0022

export MMGEN_TEST_SUITE=1
export MMGEN_NO_LICENSE=1
export PYTHONPATH=.

test_py='test/test.py -n'
objtest_py='test/objtest.py'
objattrtest_py='test/objattrtest.py'
colortest_py='test/colortest.py'
unit_tests_py='test/unit_tests.py --names --quiet'
tooltest_py='test/tooltest.py'
tooltest2_py='test/tooltest2.py --names --quiet'
gentest_py='test/gentest.py --quiet'
scrambletest_py='test/scrambletest.py'
altcoin_mod_opts='--quiet'
mmgen_tool='cmds/mmgen-tool'
mmgen_keygen='cmds/mmgen-keygen'
python='python3'
rounds=100 rounds_min=20 rounds_mid=250 rounds_max=500

dfl_tests='dep misc obj color unit hash ref altref alts xmr eth autosign btc btc_tn btc_rt bch bch_rt ltc ltc_rt tool tool2 gen'
extra_tests='dep autosign_btc autosign_live ltc_tn bch_tn'
noalt_tests='dep misc obj color unit hash ref autosign_btc btc btc_tn btc_rt tool tool2 gen'
quick_tests='dep misc obj color unit hash ref altref alts xmr eth autosign btc btc_rt tool tool2 gen'
qskip_tests='btc_tn bch bch_rt ltc ltc_rt'

PROGNAME=$(basename $0)
while getopts hAbCdDfFi:I:lNOps:tvV OPT
do
	case "$OPT" in
	h)  printf "  %-16s Test MMGen release\n" "${PROGNAME}:"
		echo   "  USAGE:           $PROGNAME [options] [tests or test group]"
		echo   "  OPTIONS: -h      Print this help message"
		echo   "           -A      Skip tests requiring altcoin modules or daemons"
		echo   "           -b      Buffer keypresses for all invocations of 'test/test.py'"
		echo   "           -C      Run tests in coverage mode"
		echo   "           -d      Enable Python Development Mode"
		echo   "           -D      Run tests in deterministic mode"
		echo   "           -f      Speed up the tests by using fewer rounds"
		echo   "           -F      Reduce rounds even further"
		echo   "           -i BRANCH Create and install Python package from cloned BRANCH, then"
		echo   "                   run tests in installed package"
		echo   "           -I BRANCH Like '-i', but install the package without running the tests"
		echo   "           -l      List the test name symbols"
		echo   "           -N      Pass the --no-timings switch to test/test.py"
		echo   "           -O      Use pexpect.spawn rather than popen_spawn where applicable"
		echo   "           -p      Pause between tests"
		echo   "           -s LIST Skip tests in LIST (space-separated)"
		echo   "           -t      Print the tests without running them"
		echo   "           -v      Run test/test.py with '--exact-output' and other commands"
		echo   "                   with '--verbose' switch"
		echo   "           -V      Run test/test.py and other commands with '--verbose' switch"
		echo
		echo   "  AVAILABLE TESTS:"
		echo   "     obj      - data objects"
		echo   "     color    - color handling"
		echo   "     unit     - unit tests"
		echo   "     hash     - internal hash function implementations"
		echo   "     ref      - reference file checks"
		echo   "     altref   - altcoin reference file checks"
		echo   "     alts     - operations for all supported gen-only altcoins"
		echo   "     xmr      - Monero xmrwallet operations"
		echo   "     eth      - operations for Ethereum and Ethereum Classic"
		echo   "     autosign - autosign"
		echo   "     btc      - bitcoin"
		echo   "     btc_tn   - bitcoin testnet"
		echo   "     btc_rt   - bitcoin regtest"
		echo   "     bch      - bitcoin cash (BCH)"
		echo   "     bch_tn   - bitcoin cash (BCH) testnet"
		echo   "     bch_rt   - bitcoin cash (BCH) regtest"
		echo   "     ltc      - litecoin"
		echo   "     ltc_tn   - litecoin testnet"
		echo   "     ltc_rt   - litecoin regtest"
		echo   "     tool     - tooltest (all supported coins)"
		echo   "     tool2    - tooltest2 (all supported coins)"
		echo   "     gen      - gentest (all supported coins)"
		echo   "     misc     - miscellaneous tests that don't fit in the above categories"
		echo
		echo   "  AVAILABLE TEST GROUPS:"
		echo   "     default  - All tests minus the extra tests"
		echo   "     extra    - All tests minus the default tests"
		echo   "     noalt    - BTC-only tests"
		echo   "     quick    - Default tests minus btc_tn, bch, bch_rt, ltc and ltc_rt"
		echo   "     qskip    - The tests skipped in the 'quick' test group"
		echo
		echo   "  By default, all tests are run"
		exit ;;
	A)  SKIP_ALT_DEP=1
		test_py+=" --no-altcoin"
		unit_tests_py+=" --no-altcoin-deps"
		scrambletest_py+=" --no-altcoin" ;;
	b)  test_py+=" --buf-keypress" ;;
	C)  mkdir -p 'test/trace'
		touch 'test/trace.acc'
		test_py+=" --coverage"
		tooltest_py+=" --coverage"
		tooltest2_py+=" --fork --coverage"
		scrambletest_py+=" --coverage"
		python="python3 -m trace --count --file=test/trace.acc --coverdir=test/trace"
		unit_tests_py="$python $unit_tests_py"
		objtest_py="$python $objtest_py"
		objattrtest_py="$python $objattrtest_py"
		gentest_py="$python $gentest_py"
		mmgen_tool="$python $mmgen_tool"
		mmgen_keygen="$python $mmgen_keygen" ;&
	d)  export PYTHONDEVMODE=1
		export PYTHONWARNINGS='error' ;;
	D)  export MMGEN_TEST_SUITE_DETERMINISTIC=1
		export MMGEN_DISABLE_COLOR=1 ;;
	f)  FAST=1 rounds=10 rounds_min=3 rounds_mid=25 rounds_max=50 unit_tests_py+=" --fast" ;;
	F)  FAST=1 rounds=3 rounds_min=1 rounds_mid=3 rounds_max=5 unit_tests_py+=" --fast" ;;
	i)  INSTALL=$OPTARG ;;
	I)  INSTALL=$OPTARG INSTALL_ONLY=1 ;;
	l)  echo -e "Default tests:\n  $dfl_tests"
		echo -e "Extra tests:\n  $extra_tests"
		echo -e "'noalt' test group:\n  $noalt_tests"
		echo -e "'quick' test group:\n  $quick_tests"
		echo -e "'qskip' test group:\n  $qskip_tests"
		exit ;;
	N)  test_py+=" --no-timings" ;;
	O)  test_py+=" --pexpect-spawn" ;;
	p)  PAUSE=1 ;;
	s)  SKIP_LIST+=" $OPTARG" ;;
	t)  LIST_CMDS=1 ;;
	v)  EXACT_OUTPUT=1 test_py+=" --exact-output" ;&
	V)  VERBOSE='--verbose'
		[ "$EXACT_OUTPUT" ] || test_py+=" --verbose"
		unit_tests_py="${unit_tests_py/--quiet/--verbose}"
		altcoin_mod_opts="${altcoin_mod_opts/--quiet/--verbose}"
		tooltest2_py="${tooltest2_py/--quiet/--verbose}"
		gentest_py="${gentest_py/--quiet/--verbose}"
		tooltest_py+=" --verbose"
		mmgen_tool+=" --verbose"
		objattrtest_py+=" --verbose"
		scrambletest_py+=" --verbose" ;;
	*)  exit ;;
	esac
done

[ "$MMGEN_DISABLE_COLOR" ] || {
	RED="\e[31;1m" GREEN="\e[32;1m" YELLOW="\e[33;1m" BLUE="\e[34;1m" MAGENTA="\e[35;1m" CYAN="\e[36;1m"
	RESET="\e[0m"
}

[ "$MSYS2" -a ! "$FAST" ] && tooltest2_py+=' --fork'
[ "$EXACT_OUTPUT" -o "$VERBOSE" ] || objtest_py+=" -S"

shift $((OPTIND-1))

case $1 in
	'')        tests=$dfl_tests ;;
	'default') tests=$dfl_tests ;;
	'extra')   tests=$extra_tests ;;
	'noalt')   tests=$noalt_tests
				SKIP_ALT_DEP=1
				test_py+=" --no-altcoin"
				unit_tests_py+=" --no-altcoin-deps"
				scrambletest_py+=" --no-altcoin" ;;
	'quick')   tests=$quick_tests ;;
	'qskip')   tests=$qskip_tests ;;
	*)         tests="$*" ;;
esac

[ "$INSTALL" ] && {
	BRANCH=$INSTALL
	BRANCHES=$(git branch)
	FOUND_BRANCH=$(for b in ${BRANCHES/\*}; do [ "$b" == "$BRANCH" ] && echo ok; done)
	[ "$FOUND_BRANCH" ] || { echo "Branch '$BRANCH' not found!"; exit; }
}

set -e

check() {
	[ "$BRANCH" ] || { echo 'No branch specified.  Exiting'; exit; }
	[ "$(git diff $BRANCH)" == "" ] || {
		echo "Unmerged changes from branch '$BRANCH'. Exiting"
		exit 1
	}
	git diff $BRANCH >/dev/null 2>&1 || exit 1
}
uninstall() {
	set +e
	eval "$SUDO ./scripts/uninstall-mmgen.py"
	[ "$?" -ne 0 ] && { echo 'Uninstall failed, but proceeding anyway'; sleep 1; }
	set -e
}
install() {
	set -x
	eval "$SUDO rm -rf .test-release"
	git clone --branch $BRANCH --single-branch . .test-release
	(
		cd .test-release
		./setup.py sdist
		mkdir pydist && cd pydist
		if [ "$MSYS2" ]; then unzip ../dist/mmgen-*.zip; else tar zxvf ../dist/mmgen-*gz; fi
		cd mmgen-*
		eval "$SUDO ./setup.py clean --all"
		[ "$MSYS2" ] && ./setup.py build --compiler=mingw32
		eval "$SUDO ./setup.py install --force"
	)
	set +x
}

do_test() {
	set +x
	tests="t_$1"
	skips="t_$1_skip"

	while read skip test; do
		[ "$test" ] || continue
		echo "${!skips}" | grep -q $skip && continue

		if [ "$LIST_CMDS" ]; then
			echo $test
		else
			test_disp=$YELLOW${test/\#/$RESET$MAGENTA\#}$RESET
			if [ "${test:0:1}" == '#' ]; then
				echo -e "$test_disp"
			else
				echo -e "${GREEN}Running:$RESET $test_disp"
				eval "$test" || {
					echo -e $RED"test-release.sh: test '$CUR_TEST' failed at command '$test'"$RESET
					exit 1
				}
			fi
		fi
	done <<<${!tests}
}

i_misc='Miscellaneous'
s_misc='Testing various subsystems'
t_misc="
	- python3 -m mmgen.altcoin $altcoin_mod_opts
"
f_misc='Miscellaneous tests completed'

i_obj='Data object'
s_obj='Testing data objects'
t_obj="
	- $objtest_py --coin=btc
	- $objtest_py --getobj --coin=btc
	- $objtest_py --coin=btc --testnet=1
	- $objtest_py --coin=ltc
	- $objtest_py --coin=ltc --testnet=1
	- $objtest_py --coin=eth
	- $objattrtest_py
"
f_obj='Data object tests completed'

[ "$PYTHONOPTIMIZE" ] && {
	echo -e "${YELLOW}PYTHONOPTIMIZE set, skipping object tests$RESET"
	t_obj_skip='-'
}

i_color='Color'
s_color='Testing terminal colors'
t_color="- $colortest_py"
f_color='Terminal color tests completed'

i_dep='Dependency'
s_dep='Testing for installed dependencies'
t_dep="- $unit_tests_py testdep dep daemon.exec"
f_dep='Dependency tests completed'

i_unit='Unit'
s_unit='The bitcoin and bitcoin-bchn mainnet daemons must be running for the following tests'
t_unit="- $unit_tests_py --exclude testdep,dep,daemon"
f_unit='Unit tests completed'

i_hash='Internal hash function implementations'
s_hash='Testing internal hash function implementations'
t_hash="
	256    $python test/hashfunc.py sha256 $rounds_max
	512    $python test/hashfunc.py sha512 $rounds_max # native SHA512 - not used by the MMGen wallet
	keccak $python test/hashfunc.py keccak $rounds_max
"
f_hash='Hash function tests completed'

[ "$ARM32" ] && t_hash_skip='512'        # gmpy produces invalid init constants
[ "$MSYS2" ] && t_hash_skip='512 keccak' # 2:py_long_long issues, 3:no pysha3 for keccak reference
[ "$SKIP_ALT_DEP" ] && t_hash_skip+=' keccak'

i_ref='Miscellaneous reference data'
s_ref='The following tests will test some generated values against reference data'
t_ref="
	- $scrambletest_py
"
f_ref='Miscellaneous reference data tests completed'

i_altref='Altcoin reference file'
s_altref='The following tests will test some generated altcoin files against reference data'
t_altref="
	- $test_py ref_altcoin # generated addrfiles verified against checksums
"
f_altref='Altcoin reference file tests completed'

i_alts='Gen-only altcoin'
s_alts='The following tests will test generation operations for all supported altcoins'
t_alts="
	- # speed tests, no verification:
	- $gentest_py --coin=etc 1 $rounds
	- $gentest_py --coin=etc --use-internal-keccak-module 1 $rounds_min
	- $gentest_py --coin=eth 1 $rounds
	- $gentest_py --coin=eth --use-internal-keccak-module 1 $rounds_min
	- $gentest_py --coin=xmr 1 $rounds
	- $gentest_py --coin=xmr --use-internal-keccak-module 1 $rounds_min
	- $gentest_py --coin=zec 1 $rounds
	- $gentest_py --coin=zec --type=zcash_z 1 $rounds_mid
	- # verification against external libraries and tools:
	- #   pycoin
	- $gentest_py --all-coins --type=legacy 1:pycoin $rounds
	- $gentest_py --all-coins --type=compressed 1:pycoin $rounds
	- $gentest_py --all-coins --type=segwit 1:pycoin $rounds
	- $gentest_py --all-coins --type=bech32 1:pycoin $rounds

	- $gentest_py --all-coins --type=legacy --testnet=1 1:pycoin $rounds
	- $gentest_py --all-coins --type=compressed --testnet=1 1:pycoin $rounds
	- $gentest_py --all-coins --type=segwit --testnet=1 1:pycoin $rounds
	- $gentest_py --all-coins --type=bech32 --testnet=1 1:pycoin $rounds
	- #   keyconv
	- $gentest_py --all-coins --type=legacy 1:keyconv $rounds
	- $gentest_py --all-coins --type=compressed 1:keyconv $rounds
	e #   ethkey
	e $gentest_py --coin=eth 1:ethkey $rounds
	e $gentest_py --coin=eth --use-internal-keccak-module 2:ethkey $rounds_mid
	m #   moneropy
	m $gentest_py --coin=xmr all:moneropy $rounds_mid # very slow, please be patient!
	z #   zcash-mini
	z $gentest_py --coin=zec --type=zcash_z all:zcash-mini $rounds_mid
"

[ "$MSYS2" ] && t_alts_skip='m z'  # no moneropy (pysha3), zcash-mini (golang)
[ "$ARM32" -o "$ARM64" ] && t_alts_skip='z e'

f_alts='Gen-only altcoin tests completed'

create_tmpdir() {
	if [ "$MSYS2" ]; then
		TMPDIR='/tmp/mmgen-test-release'
	else
		TMPDIR='/tmp/mmgen-test-release-'$(cat /dev/urandom | base32 - | head -n1 | cut -b 1-16)
	fi
	mkdir -p $TMPDIR
}

rm -rf /tmp/mmgen-test-release*
create_tmpdir

i_xmr='Monero'
s_xmr='Testing Monero operations'
t_xmr="
	- $test_py --coin=xmr
"
f_xmr='Monero tests completed'

i_eth='Ethereum'
s_eth='Testing transaction and tracking wallet operations for Ethereum'
t_eth="
	oe     $test_py --coin=eth --daemon-id=openethereum ethdev
	geth   $test_py --coin=eth --daemon-id=geth ethdev
	parity $test_py --coin=etc ethdev
"
f_eth='Ethereum tests completed'

[ "$FAST" ] && t_eth_skip='oe'
[ "$ARM32" -o "$ARM64" ] && t_eth_skip='oe parity'

i_autosign='Autosign'
s_autosign='The bitcoin, bitcoin-bchn and litecoin mainnet and testnet daemons must be running for the following test'
t_autosign="- $test_py autosign"
f_autosign='Autosign test completed'

i_autosign_btc='Autosign BTC'
s_autosign_btc='The bitcoin mainnet and testnet daemons must be running for the following test'
t_autosign_btc="- $test_py autosign_btc"
f_autosign_btc='Autosign BTC test completed'

i_autosign_live='Autosign Live'
s_autosign_live="The bitcoin mainnet and testnet daemons must be running for the following test\n"
s_autosign_live+="${YELLOW}Mountpoint, '/etc/fstab' and removable device must be configured "
s_autosign_live+="as described in 'mmgen-autosign --help'${RESET}"
t_autosign_live="- $test_py autosign_live"
f_autosign_live='Autosign Live test completed'

i_btc='Bitcoin mainnet'
s_btc='The bitcoin (mainnet) daemon must both be running for the following tests'
t_btc="
	- $test_py --exclude regtest,autosign,ref_altcoin
	- $test_py --segwit
	- $test_py --segwit-random
	- $test_py --bech32
	- $python scripts/compute-file-chksum.py $REFDIR/*testnet.rawtx >/dev/null 2>&1
"
f_btc='Bitcoin mainnet tests completed'

i_btc_tn='Bitcoin testnet'
s_btc_tn='The bitcoin testnet daemon must both be running for the following tests'
t_btc_tn="
	- $test_py --testnet=1
	- $test_py --testnet=1 --segwit
	- $test_py --testnet=1 --segwit-random
	- $test_py --testnet=1 --bech32
"
f_btc_tn='Bitcoin testnet tests completed'

i_btc_rt='Bitcoin regtest'
s_btc_rt="The following tests will test MMGen's regtest (Bob and Alice) mode"
t_btc_rt="- $test_py regtest"
f_btc_rt='Regtest (Bob and Alice) mode tests for BTC completed'

i_bch='BitcoinCashNode (BCH) mainnet'
s_bch='The bitcoin-bchn mainnet daemon must both be running for the following tests'
t_bch="- $test_py --coin=bch --exclude regtest"
f_bch='BitcoinCashNode (BCH) mainnet tests completed'

i_bch_tn='BitcoinCashNode (BCH) testnet'
s_bch_tn='The bitcoin-bchn testnet daemon must both be running for the following tests'
t_bch_tn="- $test_py --coin=bch --testnet=1 --exclude regtest"
f_bch_tn='BitcoinCashNode (BCH) testnet tests completed'

i_bch_rt='BitcoinCashNode (BCH) regtest'
s_bch_rt="The following tests will test MMGen's regtest (Bob and Alice) mode"
t_bch_rt="- $test_py --coin=bch regtest"
f_bch_rt='Regtest (Bob and Alice) mode tests for BCH completed'

i_ltc='Litecoin'
s_ltc='The litecoin mainnet daemon must both be running for the following tests'
t_ltc="
	- $test_py --coin=ltc --exclude regtest
	- $test_py --coin=ltc --segwit
	- $test_py --coin=ltc --segwit-random
	- $test_py --coin=ltc --bech32
"
f_ltc='Litecoin mainnet tests completed'

i_ltc_tn='Litecoin testnet'
s_ltc_tn='The litecoin testnet daemon must both be running for the following tests'
t_ltc_tn="
	- $test_py --coin=ltc --testnet=1 --exclude regtest
	- $test_py --coin=ltc --testnet=1 --segwit
	- $test_py --coin=ltc --testnet=1 --segwit-random
	- $test_py --coin=ltc --testnet=1 --bech32
"
f_ltc_tn='Litecoin testnet tests completed'

i_ltc_rt='Litecoin regtest'
s_ltc_rt="The following tests will test MMGen's regtest (Bob and Alice) mode"
t_ltc_rt="- $test_py --coin=ltc regtest"
f_ltc_rt='Regtest (Bob and Alice) mode tests for LTC completed'

i_tool2='Tooltest2'
s_tool2="The following tests will run '$tooltest2_py' for all supported coins"
t_tool2="
	- $tooltest2_py --tool-api # test the tool_api subsystem
	- $tooltest2_py --tool-api --testnet=1
	e $tooltest2_py --tool-api --coin=eth
	a $tooltest2_py --tool-api --coin=xmr
	a $tooltest2_py --tool-api --coin=zec
	- $tooltest2_py
	- $tooltest2_py --testnet=1
	a $tooltest2_py --coin=ltc
	a $tooltest2_py --coin=ltc --testnet=1
	a $tooltest2_py --coin=bch
	a $tooltest2_py --coin=bch --testnet=1
	a $tooltest2_py --coin=zec
	a $tooltest2_py --coin=xmr
	a $tooltest2_py --coin=dash
	e $tooltest2_py --coin=eth
	e $tooltest2_py --coin=eth --testnet=1
	e $tooltest2_py --coin=eth --token=mm1
	e $tooltest2_py --coin=eth --token=mm1 --testnet=1
	e $tooltest2_py --coin=etc
	- $tooltest2_py --fork # run once with --fork so commands are actually executed
"
f_tool2='tooltest2 tests completed'
[ "$SKIP_ALT_DEP" ] && t_tool2_skip='a e' # skip ETH,ETC: txview requires py_ecc

i_tool='Tooltest'
s_tool="The following tests will run '$tooltest_py' for all supported coins"
t_tool="
	- $tooltest_py --coin=btc cryptocoin
	- $tooltest_py --coin=btc mnemonic
	a $tooltest_py --coin=ltc cryptocoin
	a $tooltest_py --coin=eth cryptocoin
	a $tooltest_py --coin=etc cryptocoin
	a $tooltest_py --coin=dash cryptocoin
	a $tooltest_py --coin=doge cryptocoin
	a $tooltest_py --coin=emc cryptocoin
	a $tooltest_py --coin=xmr cryptocoin
	a $tooltest_py --coin=zec cryptocoin
	z $tooltest_py --coin=zec --type=zcash_z cryptocoin
"
[ "$MSYS2" -o "$ARM32" -o "$ARM64" ] && t_tool_skip='z'
[ "$SKIP_ALT_DEP" ] && t_tool_skip='a z'

f_tool='tooltest tests completed'

i_gen='Gentest'
s_gen="The following tests will run '$gentest_py' for configured coins and address types"
t_gen="
	- # speed tests, no verification:
	- $gentest_py --coin=btc 1 $rounds
	- $gentest_py --coin=btc --type=compressed 1 $rounds
	- $gentest_py --coin=btc --type=segwit 1 $rounds
	- $gentest_py --coin=btc --type=bech32 1 $rounds
	a $gentest_py --coin=ltc 1 $rounds
	a $gentest_py --coin=ltc --type=compressed 1 $rounds
	a $gentest_py --coin=ltc --type=segwit 1 $rounds
	a $gentest_py --coin=ltc --type=bech32 1 $rounds
	- # wallet dumps:
	- $gentest_py --type=compressed 1 $REFDIR/btcwallet.dump
	- $gentest_py --type=segwit 1 $REFDIR/btcwallet-segwit.dump
	- $gentest_py --type=bech32 1 $REFDIR/btcwallet-bech32.dump
	- $gentest_py --type=compressed --testnet=1 1 $REFDIR/btcwallet-testnet.dump
	a $gentest_py --coin=ltc --type=compressed 1 $REFDIR/litecoin/ltcwallet.dump
	a $gentest_py --coin=ltc --type=segwit 1 $REFDIR/litecoin/ltcwallet-segwit.dump
	a $gentest_py --coin=ltc --type=bech32 1 $REFDIR/litecoin/ltcwallet-bech32.dump
	a $gentest_py --coin=ltc --type=compressed --testnet=1 1 $REFDIR/litecoin/ltcwallet-testnet.dump
	- # libsecp256k1 vs python-ecdsa:
	- $gentest_py 1:2 $rounds
	- $gentest_py --type=segwit 1:2 $rounds
	- $gentest_py --type=bech32 1:2 $rounds
	- $gentest_py --testnet=1 1:2 $rounds
	- $gentest_py --testnet=1 --type=segwit 1:2 $rounds
	a $gentest_py --coin=ltc 1:2 $rounds
	a $gentest_py --coin=ltc --type=segwit 1:2 $rounds
	a $gentest_py --coin=ltc --testnet=1 1:2 $rounds
	a $gentest_py --coin=ltc --testnet=1 --type=segwit 1:2 $rounds
	a # all backends vs pycoin:
	a $gentest_py all:pycoin $rounds
"

[ "$SKIP_ALT_DEP" ] && t_gen_skip='a'
f_gen='gentest tests completed'

[ -d .git -a -n "$INSTALL"  -a -z "$LIST_CMDS" ] && {
	check
	uninstall
	install
	cd .test-release/pydist/mmgen-*
}
[ "$INSTALL_ONLY" ] && exit

prompt_skip() {
	echo -n "Enter 's' to skip, or ENTER to continue: "; read -n1; echo
	[ "$REPLY" == 's' ] && return 0
	return 1
}

run_tests() {
	[ "$LIST_CMDS" ] || echo "Running tests: $1"
	for t in $1; do
		if [ "$SKIP_ALT_DEP" ]; then
			ok=$(for a in $noalt_tests; do if [ $t == $a ]; then echo 'ok'; fi; done)
			if [ ! "$ok" ]; then
				echo -e "${BLUE}Skipping altcoin test '$t'$RESET"
				continue
			fi
		fi
		if [ "$LIST_CMDS" ]; then
			eval echo -e '\\n#' $(echo \$i_$t) "\($t\)"
		else
			eval echo -e "'\n'"\${GREEN}'###' Running $(echo \$i_$t) tests\$RESET
			eval echo -e $(echo \$s_$t)
		fi
		[ "$PAUSE" ] && prompt_skip && continue
		CUR_TEST=$t
		do_test $t
		[ "$LIST_CMDS" ] || eval echo -e $(echo \$f_$t)
	done
}

check_args() {
	for i in $tests; do
		echo "$dfl_tests $extra_tests" | grep -q "\<$i\>" || {
			echo "$i: unrecognized argument"
			exit 1
		}
	done
}

remove_skipped_tests() {
	tests=$(for t in $tests; do
		[ "$(for s in $SKIP_LIST; do [ $t == $s ] && echo y; done)" ] && continue
		echo $t
	done)
	tests=$(echo $tests)
}

remove_skipped_tests

check_args

start_time=$(date +%s)

run_tests "$tests"

elapsed=$(($(date +%s)-start_time))
elapsed_fmt=$(printf %02d:%02d $((elapsed/60)) $((elapsed%60)))

[ "$LIST_CMDS" ] || {
	if [ "$MMGEN_TEST_SUITE_DETERMINISTIC" ]; then
		echo -e "${GREEN}All OK"
	else
		echo -e "${GREEN}All OK.  Total elapsed time: $elapsed_fmt$RESET"
	fi
}

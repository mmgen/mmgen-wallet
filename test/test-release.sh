#!/bin/bash
# Tested on Linux, Armbian, Raspbian, MSYS2

REFDIR='test/ref'
SUDO='sudo'

if [ "$(uname -m)" == 'armv7l' ]; then
	ARM32=1
elif uname -a | grep -q 'MSYS'; then
	SUDO='' MSYS2=1;
fi

RED="\e[31;1m" GREEN="\e[32;1m" YELLOW="\e[33;1m" BLUE="\e[34;1m" MAGENTA="\e[35;1m" CYAN="\e[36;1m"
RESET="\e[0m"

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
altcoin_py='mmgen/altcoin.py --quiet'
mmgen_tool='cmds/mmgen-tool'
mmgen_keygen='cmds/mmgen-keygen'
python='python3'
rounds=100 rounds_min=20 rounds_mid=250 rounds_max=500
xmr_addrs='3,99,2,22-24,101-104'

dfl_tests='misc obj color unit hash ref altref alts xmr eth autosign btc btc_tn btc_rt bch bch_rt ltc ltc_rt tool tool2 gen'
extra_tests='autosign_minimal autosign_live etc ltc_tn bch_tn'
noalt_tests='misc obj color unit hash ref autosign_minimal btc btc_tn btc_rt tool tool2 gen'
quick_tests='misc obj color unit hash ref altref alts xmr eth autosign btc btc_rt tool tool2 gen'
qskip_tests='btc_tn bch bch_rt ltc ltc_rt'

PROGNAME=$(basename $0)
while getopts hbCfFi:I:lOpRtvV OPT
do
	case "$OPT" in
	h)  printf "  %-16s Test MMGen release\n" "${PROGNAME}:"
		echo   "  USAGE:           $PROGNAME [options] [tests or test group]"
		echo   "  OPTIONS: '-h'  Print this help message"
		echo   "           '-b'  Buffer keypresses for all invocations of 'test/test.py'"
		echo   "           '-C'  Run tests in coverage mode"
		echo   "           '-f'  Speed up the tests by using fewer rounds"
		echo   "           '-F'  Reduce rounds even further"
		echo   "           '-i'  Create and install Python package, then run tests.  A branch"
		echo   "                 must be supplied as a parameter"
		echo   "           '-I'  Like '-i', but install the package without running the tests"
		echo   "           '-l'  List the test name symbols"
		echo   "           '-O'  Use pexpect.spawn rather than popen_spawn for applicable tests"
		echo   "           '-p'  Pause between tests"
		echo   "           '-R'  Don't remove temporary files after program has exited"
		echo   "           '-t'  Print the tests without running them"
		echo   "           '-v'  Run test/test.py with '--exact-output' and other commands with"
		echo   "                 '--verbose' switch"
		echo   "           '-V'  Run test/test.py and other commands with '--verbose' switch"
		echo
		echo   "  AVAILABLE TESTS:"
		echo   "     obj      - data objects"
		echo   "     color    - color handling"
		echo   "     unit     - unit tests"
		echo   "     hash     - internal hash function implementations"
		echo   "     ref      - reference file checks"
		echo   "     altref   - altcoin reference file checks"
		echo   "     alts     - operations for all supported gen-only altcoins"
		echo   "     xmr      - operations for Monero"
		echo   "     eth      - operations for Ethereum"
		echo   "     etc      - operations for Ethereum Classic"
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
	f)  FAST=1 rounds=10 rounds_min=3 rounds_mid=25 rounds_max=50 xmr_addrs='3,23' unit_tests_py+=" --fast" ;;
	F)  FAST=1 rounds=3 rounds_min=1 rounds_mid=3 rounds_max=5 xmr_addrs='3,23' unit_tests_py+=" --fast" ;;
	i)  INSTALL=$OPTARG ;;
	I)  INSTALL=$OPTARG INSTALL_ONLY=1 ;;
	l)  echo -e "Default tests:\n  $dfl_tests"
		echo -e "Extra tests:\n  $extra_tests"
		echo -e "'noalt' test group:\n  $noalt_tests"
		echo -e "'quick' test group:\n  $quick_tests"
		echo -e "'qskip' test group:\n  $qskip_tests"
		exit ;;
	O)  test_py+=" --pexpect-spawn" ;;
	p)  PAUSE=1 ;;
	R)  NO_TMPFILE_REMOVAL=1 ;;
	t)  LIST_CMDS=1 ;;
	v)  EXACT_OUTPUT=1 test_py+=" --exact-output" ;&
	V)  VERBOSE=1 [ "$EXACT_OUTPUT" ] || test_py+=" --verbose"
		unit_tests_py="${unit_tests_py/--quiet/--verbose}"
		altcoin_py="${altcoin_py/--quiet/--verbose}"
		tooltest2_py="${tooltest2_py/--quiet/--verbose}"
		gentest_py="${gentest_py/--quiet/--verbose}"
		tooltest_py+=" --verbose"
		mmgen_tool+=" --verbose"
		objattrtest_py+=" --verbose"
		scrambletest_py+=" --verbose" ;;
	*)  exit ;;
	esac
done

[ "$MSYS2" -a ! "$FAST" ] && tooltest2_py+=' --fork'
[ "$EXACT_OUTPUT" -o "$VERBOSE" ] || objtest_py+=" -S"

shift $((OPTIND-1))

case $1 in
	'')        tests=$dfl_tests ;;
	'default') tests=$dfl_tests ;;
	'extra')   tests=$extra_tests ;;
	'noalt')   tests=$noalt_tests ;;
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
		exit
	}
	git diff $BRANCH >/dev/null 2>&1 || exit
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
	tests=$(eval echo \"'$'"t_$1"\")
	skips=$(eval echo \"'$'"t_$1_skip"\")

	declare -a tests_arr

	n=0
	while read test; do
		tests_arr[n]="$test"
		let n+=1
	done <<-EOF
	$tests
	EOF

	n=0
	for test in "${tests_arr[@]}"; do
		[ -z "$test" ] && continue
		test_disp=$YELLOW${test/\#/$RESET$MAGENTA\#}$RESET
		[ "${test:0:1}" == '#' ] && {
			[ "$LIST_CMDS" ] || echo -e "$test_disp"
			continue
		}
		let n+=1
		echo $skips | grep -q "\<$n\>" && continue
		if [ "$LIST_CMDS" ]; then
			echo $test
		else
			echo -e "${GREEN}Running:$RESET $test_disp"
		fi
#		continue
		[ "$LIST_CMDS" ] || eval "$test" || {
			echo -e $RED"test-release.sh: test '$CUR_TEST' failed at command '$test'"$RESET
			exit 1
		}
	done
}

i_misc='Miscellaneous'
s_misc='Testing various subsystems'
t_misc="
	$altcoin_py
"
f_misc='Miscellaneous tests completed'

i_obj='Data object'
s_obj='Testing data objects'
t_obj="
	$objtest_py --coin=btc
	$objtest_py --coin=btc --testnet=1
	$objtest_py --coin=ltc
	$objtest_py --coin=ltc --testnet=1
	$objtest_py --coin=eth
	$objattrtest_py
"
f_obj='Data object tests completed'

i_color='Color'
s_color='Testing terminal colors'
t_color="$colortest_py"
f_color='Terminal color tests completed'

i_unit='Unit'
s_unit='The bitcoin and bitcoin-abc mainnet daemons must be running for the following tests'
t_unit="$unit_tests_py"
f_unit='Unit tests completed'

i_hash='Internal hash function implementations'
s_hash='Testing internal hash function implementations'
t_hash="
	$python test/hashfunc.py sha256 $rounds_max
	$python test/hashfunc.py sha512 $rounds_max # native SHA512 - not used by the MMGen wallet
	$python test/hashfunc.py keccak $rounds_max
"
f_hash='Hash function tests completed'

[ "$ARM32" ] && t_hash_skip='2' # gmpy produces invalid init constants
[ "$MSYS2" ] && t_hash_skip='2 3' # 2:py_long_long issues, 3:no pysha3 for keccak reference

i_ref='Miscellaneous reference data'
s_ref='The following tests will test some generated values against reference data'
t_ref="
	$scrambletest_py
"
f_ref='Miscellaneous reference data tests completed'

i_altref='Altcoin reference file'
s_altref='The following tests will test some generated altcoin files against reference data'
t_altref="
	$test_py ref_altcoin # generated addrfiles verified against checksums
"
f_altref='Altcoin reference file tests completed'

i_alts='Gen-only altcoin'
s_alts='The following tests will test generation operations for all supported altcoins'
t_alts="
	# speed tests, no verification:
	$gentest_py --coin=etc 2 $rounds
	$gentest_py --coin=etc --use-internal-keccak-module 2 $rounds_min
	$gentest_py --coin=eth 2 $rounds
	$gentest_py --coin=eth --use-internal-keccak-module 2 $rounds_min
	$gentest_py --coin=xmr 2 $rounds
	$gentest_py --coin=xmr --use-internal-keccak-module 2 $rounds_min
	$gentest_py --coin=zec 2 $rounds
	$gentest_py --coin=zec --type=zcash_z 2 $rounds_mid
	# verification against external libraries and tools:
	#   pycoin
	$gentest_py --all --type=legacy 2:pycoin $rounds
	$gentest_py --all --type=compressed 2:pycoin $rounds
	$gentest_py --all --type=segwit 2:pycoin $rounds
	$gentest_py --all --type=bech32 2:pycoin $rounds

	$gentest_py --all --type=legacy --testnet=1 2:pycoin $rounds
	$gentest_py --all --type=compressed --testnet=1 2:pycoin $rounds
	$gentest_py --all --type=segwit --testnet=1 2:pycoin $rounds
	$gentest_py --all --type=bech32 --testnet=1 2:pycoin $rounds
	#   keyconv
	$gentest_py --all --type=legacy 2:keyconv $rounds
	$gentest_py --all --type=compressed 2:keyconv $rounds
"

[ "$MSYS2" ] || { # no moneropy (pysha3), zcash-mini (golang), ethkey (?)
	t_alts+="
		#   moneropy
		$gentest_py --all --coin=xmr 2:moneropy $rounds_min # very slow, be patient!
		#   zcash-mini
		$gentest_py --all 2:zcash-mini $rounds_mid
		#   ethkey
		$gentest_py --all 2:ethkey $rounds
	"
}

f_alts='Gen-only altcoin tests completed'

if [ "$NO_TMPFILE_REMOVAL" ]; then
	TMPDIR=$(echo /tmp/mmgen-test-release*)
else
	rm -rf /tmp/mmgen-test-release*
	if [ "$MSYS2" ]; then
		TMPDIR='/tmp/mmgen-test-release'
	else
		TMPDIR='/tmp/mmgen-test-release-'$(cat /dev/urandom | base32 - | head -n1 | cut -b 1-16)
	fi
	mkdir -p $TMPDIR
fi

mmgen_tool_xmr="$mmgen_tool -q --accept-defaults --outdir $TMPDIR"
i_xmr='Monero'
s_xmr='Testing key-address file generation and wallet creation and sync operations for Monero'
s_xmr='The monerod (mainnet) daemon must be running for the following tests'
t_xmr="
	mmgen-walletgen -q -r0 -p1 -Llabel --outdir $TMPDIR -o words
	$mmgen_keygen -q --accept-defaults --use-internal-keccak-module --outdir $TMPDIR --coin=xmr $TMPDIR/*.mmwords $xmr_addrs
	cs1=\$(mmgen-tool -q --accept-defaults --coin=xmr keyaddrfile_chksum $TMPDIR/*-XMR*.akeys)
	$mmgen_keygen -q --use-old-ed25519 --accept-defaults --outdir $TMPDIR --coin=xmr $TMPDIR/*.mmwords $xmr_addrs
	cs2=\$(mmgen-tool -q --accept-defaults --coin=xmr keyaddrfile_chksum $TMPDIR/*-XMR*.akeys)
	[ \"\$cs1\" == \"\$cs2\" ]
	test/start-coin-daemons.py xmr
	$mmgen_tool_xmr keyaddrlist2monerowallets $TMPDIR/*-XMR*.akeys addrs=23
	$mmgen_tool_xmr keyaddrlist2monerowallets $TMPDIR/*-XMR*.akeys addrs=103-200
	rm $TMPDIR/*-MoneroWallet*
	$mmgen_tool_xmr keyaddrlist2monerowallets $TMPDIR/*-XMR*.akeys
	$mmgen_tool_xmr syncmonerowallets $TMPDIR/*-XMR*.akeys addrs=3
	$mmgen_tool_xmr syncmonerowallets $TMPDIR/*-XMR*.akeys addrs=23-29
	$mmgen_tool_xmr syncmonerowallets $TMPDIR/*-XMR*.akeys
	test/stop-coin-daemons.py -W xmr
"
f_xmr='Monero tests completed'

[ "$xmr_addrs" == '3,23' ] && t_xmr_skip='4 9 14'

i_eth='Ethereum'
s_eth='Testing transaction and tracking wallet operations for Ethereum'
t_eth="
	$test_py --coin=eth ethdev
"
f_eth='Ethereum tests completed'

i_etc='Ethereum Classic'
s_etc='Testing transaction and tracking wallet operations for Ethereum Classic'
t_etc="
	$test_py --coin=etc ethdev
"
f_etc='Ethereum Classic tests completed'

i_autosign='Autosign'
s_autosign='The bitcoin, bitcoin-abc and litecoin mainnet and testnet daemons must be running for the following test'
t_autosign="$test_py autosign"
f_autosign='Autosign test completed'

i_autosign_minimal='Autosign Minimal'
s_autosign_minimal='The bitcoin mainnet and testnet daemons must be running for the following test'
t_autosign_minimal="$test_py autosign_minimal"
f_autosign_minimal='Autosign Minimal test completed'

i_autosign_live='Autosign Live'
s_autosign_live="The bitcoin mainnet and testnet daemons must be running for the following test\n"
s_autosign_live+="${YELLOW}Mountpoint, '/etc/fstab' and removable device must be configured "
s_autosign_live+="as described in 'mmgen-autosign --help'${RESET}"
t_autosign_live="$test_py autosign_live"
f_autosign_live='Autosign Live test completed'

i_btc='Bitcoin mainnet'
s_btc='The bitcoin (mainnet) daemon must both be running for the following tests'
t_btc="
	$test_py --exclude regtest,autosign_minimal,ref_altcoin
	$test_py --segwit
	$test_py --segwit-random
	$test_py --bech32
	$python scripts/compute-file-chksum.py $REFDIR/*testnet.rawtx >/dev/null 2>&1
"
f_btc='Bitcoin mainnet tests completed'

i_btc_tn='Bitcoin testnet'
s_btc_tn='The bitcoin testnet daemon must both be running for the following tests'
t_btc_tn="
	$test_py --testnet=1
	$test_py --testnet=1 --segwit
	$test_py --testnet=1 --segwit-random
	$test_py --testnet=1 --bech32
"
f_btc_tn='Bitcoin testnet tests completed'

i_btc_rt='Bitcoin regtest'
s_btc_rt="The following tests will test MMGen's regtest (Bob and Alice) mode"
t_btc_rt="$test_py regtest"
f_btc_rt='Regtest (Bob and Alice) mode tests for BTC completed'

i_bch='Bcash (BCH) mainnet'
s_bch='The bitcoin-abc mainnet daemon must both be running for the following tests'
t_bch="$test_py --coin=bch --exclude regtest"
f_bch='Bcash (BCH) mainnet tests completed'

i_bch_tn='Bcash (BCH) testnet'
s_bch_tn='The bitcoin-abc testnet daemon must both be running for the following tests'
t_bch_tn="$test_py --coin=bch --testnet=1 --exclude regtest"
f_bch_tn='Bcash (BCH) testnet tests completed'

i_bch_rt='Bcash (BCH) regtest'
s_bch_rt="The following tests will test MMGen's regtest (Bob and Alice) mode"
t_bch_rt="$test_py --coin=bch regtest"
f_bch_rt='Regtest (Bob and Alice) mode tests for BCH completed'

i_ltc='Litecoin'
s_ltc='The litecoin mainnet daemon must both be running for the following tests'
t_ltc="
	$test_py --coin=ltc --exclude regtest
	$test_py --coin=ltc --segwit
	$test_py --coin=ltc --segwit-random
	$test_py --coin=ltc --bech32
"
f_ltc='Litecoin mainnet tests completed'

i_ltc_tn='Litecoin testnet'
s_ltc_tn='The litecoin testnet daemon must both be running for the following tests'
t_ltc_tn="
	$test_py --coin=ltc --testnet=1 --exclude regtest
	$test_py --coin=ltc --testnet=1 --segwit
	$test_py --coin=ltc --testnet=1 --segwit-random
	$test_py --coin=ltc --testnet=1 --bech32
"
f_ltc_tn='Litecoin testnet tests completed'

i_ltc_rt='Litecoin regtest'
s_ltc_rt="The following tests will test MMGen's regtest (Bob and Alice) mode"
t_ltc_rt="$test_py --coin=ltc regtest"
f_ltc_rt='Regtest (Bob and Alice) mode tests for LTC completed'

i_tool2='Tooltest2'
s_tool2="The following tests will run '$tooltest2_py' for all supported coins"
t_tool2="
	$tooltest2_py --tool-api # test the tool_api subsystem
	$tooltest2_py --tool-api --testnet=1
	$tooltest2_py --tool-api --coin=eth
	$tooltest2_py --tool-api --coin=xmr
	$tooltest2_py --tool-api --coin=zec
	$tooltest2_py --fork # run once with --fork so commands are actually executed
	$tooltest2_py
	$tooltest2_py --testnet=1
	$tooltest2_py --coin=ltc
	$tooltest2_py --coin=ltc --testnet=1
	$tooltest2_py --coin=bch
	$tooltest2_py --coin=bch --testnet=1
	$tooltest2_py --coin=zec
	$tooltest2_py --coin=xmr
	$tooltest2_py --coin=dash
	$tooltest2_py --coin=eth
	$tooltest2_py --coin=eth --testnet=1
	$tooltest2_py --coin=eth --token=mm1
	$tooltest2_py --coin=eth --token=mm1 --testnet=1
	$tooltest2_py --coin=etc
"
f_tool2='tooltest2 tests completed'

i_tool='Tooltest'
s_tool="The following tests will run '$tooltest_py' for all supported coins"
t_tool="
	$tooltest_py --coin=btc cryptocoin
	$tooltest_py --coin=btc mnemonic
	$tooltest_py --coin=ltc cryptocoin
	$tooltest_py --coin=eth cryptocoin
	$tooltest_py --coin=etc cryptocoin
	$tooltest_py --coin=dash cryptocoin
	$tooltest_py --coin=doge cryptocoin
	$tooltest_py --coin=emc cryptocoin
	$tooltest_py --coin=zec cryptocoin
	$tooltest_py --coin=zec --type=zcash_z cryptocoin
"
[ "$MSYS2" ] && t_tool_skip='10'

f_tool='tooltest tests completed'

i_gen='Gentest'
s_gen="The following tests will run '$gentest_py' for BTC and LTC mainnet and testnet"
t_gen="
	# speed tests, no verification:
	$gentest_py --coin=btc 2 $rounds
	$gentest_py --coin=btc --type=compressed 2 $rounds
	$gentest_py --coin=btc --type=segwit 2 $rounds
	$gentest_py --coin=btc --type=bech32 2 $rounds
	$gentest_py --coin=ltc 2 $rounds
	$gentest_py --coin=ltc --type=compressed 2 $rounds
	$gentest_py --coin=ltc --type=segwit 2 $rounds
	$gentest_py --coin=ltc --type=bech32 2 $rounds
	# wallet dumps:
	$gentest_py 2 $REFDIR/btcwallet.dump
	$gentest_py --type=segwit 2 $REFDIR/btcwallet-segwit.dump
	$gentest_py --type=bech32 2 $REFDIR/btcwallet-bech32.dump
	$gentest_py --testnet=1 2 $REFDIR/btcwallet-testnet.dump
	$gentest_py --coin=ltc 2 $REFDIR/litecoin/ltcwallet.dump
	$gentest_py --coin=ltc --type=segwit 2 $REFDIR/litecoin/ltcwallet-segwit.dump
	$gentest_py --coin=ltc --type=bech32 2 $REFDIR/litecoin/ltcwallet-bech32.dump
	$gentest_py --coin=ltc --testnet=1 2 $REFDIR/litecoin/ltcwallet-testnet.dump
	# libsecp256k1 vs python-ecdsa:
	$gentest_py 1:2 $rounds
	$gentest_py --type=segwit 1:2 $rounds
	$gentest_py --type=bech32 1:2 $rounds
	$gentest_py --testnet=1 1:2 $rounds
	$gentest_py --testnet=1 --type=segwit 1:2 $rounds
	$gentest_py --coin=ltc 1:2 $rounds
	$gentest_py --coin=ltc --type=segwit 1:2 $rounds
	$gentest_py --coin=ltc --testnet=1 1:2 $rounds
	$gentest_py --coin=ltc --testnet=1 --type=segwit 1:2 $rounds
"
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
	for t in $1; do
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
		echo "$dfl_tests $extra_tests" | grep -q "\<$i\>" || { echo "$i: unrecognized argument"; exit; }
	done
}

check_args
[ "$LIST_CMDS" ] || echo "Running tests: $tests"
START=$(date +%s)
run_tests "$tests"
TIME=$(($(date +%s)-START))
MS=$(printf %02d:%02d $((TIME/60)) $((TIME%60)))

[ "$NO_TMPFILE_REMOVAL" ] || rm -rf /tmp/mmgen-test-release-*

[ "$LIST_CMDS" ] || echo -e "${GREEN}All OK.  Total elapsed time: $MS$RESET"

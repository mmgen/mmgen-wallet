#!/bin/bash
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

list_avail_tests() {
	echo   "AVAILABLE TESTS:"
	echo   "   obj      - data objects"
	echo   "   color    - color handling"
	echo   "   unit     - unit tests"
	echo   "   hash     - internal hash function implementations"
	echo   "   ref      - reference file checks"
	echo   "   altref   - altcoin reference file checks"
	echo   "   alts     - operations for all supported gen-only altcoins"
	echo   "   xmr      - Monero xmrwallet operations"
	echo   "   eth      - operations for Ethereum and Ethereum Classic"
	echo   "   autosign - autosign"
	echo   "   btc      - Bitcoin"
	echo   "   btc_tn   - Bitcoin testnet"
	echo   "   btc_rt   - Bitcoin regtest"
	echo   "   bch      - Bitcoin Cash Node (BCH)"
	echo   "   bch_tn   - Bitcoin Cash Node (BCH) testnet"
	echo   "   bch_rt   - Bitcoin Cash Node (BCH) regtest"
	echo   "   ltc      - Litecoin"
	echo   "   ltc_tn   - Litecoin testnet"
	echo   "   ltc_rt   - Litecoin regtest"
	echo   "   tool     - tooltest (all supported coins)"
	echo   "   tool2    - tooltest2 (all supported coins)"
	echo   "   gen      - gentest (all supported coins)"
	echo   "   misc     - miscellaneous tests that don't fit in the above categories"
	echo
	echo   "AVAILABLE TEST GROUPS:"
	echo   "   default  - All tests minus the extra tests"
	echo   "   extra    - All tests minus the default tests"
	echo   "   noalt    - BTC-only tests"
	echo   "   quick    - Default tests minus btc_tn, bch, bch_rt, ltc and ltc_rt"
	echo   "   qskip    - The tests skipped in the 'quick' test group"
	echo
	echo   "By default, all tests are run"
}

init_groups() {
	dfl_tests='dep misc obj color unit hash ref tool tool2 gen autosign btc btc_tn btc_rt altref alts bch bch_rt ltc ltc_rt eth xmr'
	extra_tests='dep autosign_btc autosign_live ltc_tn bch_tn'
	noalt_tests='dep misc obj color unit hash ref tool tool2 gen autosign_btc btc btc_tn btc_rt'
	quick_tests='dep misc obj color unit hash ref tool tool2 gen autosign btc btc_rt altref alts eth xmr'
	qskip_tests='btc_tn bch bch_rt ltc ltc_rt'

	[ "$MSYS2" ] && SKIP_LIST='autosign autosign_btc autosign_live'
}

init_tests() {
	REFDIR='test/ref'

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
	t_color='- test/colortest.py'
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
		256    $python test/hashfunc.py sha256 $rounds5x
		512    $python test/hashfunc.py sha512 $rounds5x # native SHA512 - not used by the MMGen wallet
		keccak $python test/hashfunc.py keccak $rounds5x
		ripemd160 $python mmgen/contrib/ripemd160.py $VERBOSE $fast_opt
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
		- $gentest_py --coin=etc 1 $rounds10x
		- $gentest_py --coin=etc --use-internal-keccak-module 1 $rounds10x
		- $gentest_py --coin=eth 1 $rounds10x
		- $gentest_py --coin=eth --use-internal-keccak-module 1 $rounds10x
		- $gentest_py --coin=xmr 1 $rounds10x
		- $gentest_py --coin=xmr --use-internal-keccak-module 1 $rounds10x
		- $gentest_py --coin=zec 1 $rounds10x
		- $gentest_py --coin=zec --type=zcash_z 1 $rounds10x
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
		- $gentest_py --all-coins --type=legacy 1:keyconv $rounds_min
		- $gentest_py --all-coins --type=compressed 1:keyconv $rounds_min
		e #   ethkey
		e $gentest_py --coin=eth 1:ethkey $rounds10x
		e $gentest_py --coin=eth --use-internal-keccak-module 2:ethkey $rounds5x
		m #   monero-python
		m $gentest_py --coin=xmr 1:monero-python $rounds100x
		M $gentest_py --coin=xmr all:monero-python $rounds_min # very slow, please be patient!
		z #   zcash-mini
		z $gentest_py --coin=zec --type=zcash_z all:zcash-mini $rounds50x
	"

	[ "$MSYS2" ] && t_alts_skip='M m z'  # no moneropy (pysha3), zcash-mini (golang)
	[ "$ARM32" ] && t_alts_skip='z e'
	[ "$FAST" ]  && t_alts_skip+=' M'
	# ARM ethkey available only on Arch Linux:
	[ \( "$ARM32" -o "$ARM64" \) -a "$DISTRO" != 'archarm' ] && t_alts_skip+=' e'

	f_alts='Gen-only altcoin tests completed'

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
	[ "$ARM32" -o "$ARM64" ] && t_eth_skip+=' parity'
	# ARM openethereum available only on ArchLinuxArm:
	[ \( "$ARM32" -o "$ARM64" \) -a "$DISTRO" != 'archarm' ] && t_eth_skip+=' oe'

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
	[ "$MSYS2" -o "$ARM32" ] && t_tool_skip='z'
	[ "$SKIP_ALT_DEP" ] && t_tool_skip='a z'

	f_tool='tooltest tests completed'

	i_gen='Gentest'
	s_gen="The following tests will run '$gentest_py' for configured coins and address types"
	t_gen="
		- # speed tests, no verification:
		- $gentest_py --coin=btc 1 $rounds10x
		- $gentest_py --coin=btc --type=compressed 1 $rounds10x
		- $gentest_py --coin=btc --type=segwit 1 $rounds10x
		- $gentest_py --coin=btc --type=bech32 1 $rounds10x
		a $gentest_py --coin=ltc 1 $rounds10x
		a $gentest_py --coin=ltc --type=compressed 1 $rounds10x
		a $gentest_py --coin=ltc --type=segwit 1 $rounds10x
		a $gentest_py --coin=ltc --type=bech32 1 $rounds10x
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
		- $gentest_py 1:2 $rounds100x
		- $gentest_py --type=segwit 1:2 $rounds100x
		- $gentest_py --type=bech32 1:2 $rounds100x
		- $gentest_py --testnet=1 1:2 $rounds100x
		- $gentest_py --testnet=1 --type=segwit 1:2 $rounds100x
		a $gentest_py --coin=ltc 1:2 $rounds100x
		a $gentest_py --coin=ltc --type=segwit 1:2 $rounds100x
		a $gentest_py --coin=ltc --testnet=1 1:2 $rounds100x
		a $gentest_py --coin=ltc --testnet=1 --type=segwit 1:2 $rounds100x
		- # all backends vs pycoin:
		- $gentest_py all:pycoin $rounds100x
	"

	[ "$SKIP_ALT_DEP" ] && t_gen_skip='a'
	f_gen='gentest tests completed'
}

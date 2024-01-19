#!/bin/bash
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

# Tested on Linux, Armbian, Raspbian, MSYS2

# cfg.sh must implement:
#   list_avail_tests()
#   init_groups()
#   init_tests()
. 'test/test-release.d/cfg.sh'

run_test() {
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

prompt_skip() {
	echo -n "Enter 's' to skip, or ENTER to continue: "; read -n1; echo
	[ "$REPLY" == 's' ] && return 0
	return 1
}

list_avail_tests() {
	echo   "AVAILABLE TESTS:"
	init_tests
	for i in $all_tests; do
		z="d_$i"
		printf "   %-8s - %s\n" $i "${!z}"
	done
	echo
	echo   "AVAILABLE TEST GROUPS:"
	while read a b c; do
		[ "$a" ] && printf "   %-8s - %s\n" $a "$c"
	done <<<$groups_desc
	echo
	echo   "By default, all tests are run"
}

run_tests() {
	[ "$LIST_CMDS" ] || echo "Running tests: $1"
	for t in $1; do
		desc_id="d_$t" desc=${!desc_id}
		if [ "$SKIP_ALT_DEP" ]; then
			ok=$(for a in $noalt_tests; do if [ $t == $a ]; then echo 'ok'; fi; done)
			if [ ! "$ok" ]; then
				echo -e "${BLUE}Skipping altcoin test '$t'$RESET"
				continue
			fi
		fi
		if [ "$LIST_CMDS" ]; then
			echo -e "\n### $t: $desc"
		else
			echo -e "\n${BLUE}Testing:$RESET $GREEN$desc$RESET"
		fi
		[ "$PAUSE" ] && prompt_skip && continue
		CUR_TEST=$t
		run_test $t
		[ "$LIST_CMDS" ] || echo -e "${BLUE}Finished testing:$RESET $GREEN$desc$RESET"
	done
}

check_tests() {
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

list_group_symbols() {
	echo -e "Default tests:\n  $dfl_tests"
	echo -e "Extra tests:\n  $extra_tests"
	echo -e "'noalt' test group:\n  $noalt_tests"
	echo -e "'quick' test group:\n  $quick_tests"
	echo -e "'qskip' test group:\n  $qskip_tests"
}

# start execution

trap 'echo -e "${GREEN}Exiting at user request$RESET"; exit' INT

umask 0022

if [ "$(uname -m)" == 'armv7l' ]; then
	ARM32=1
elif [ "$(uname -m)" == 'aarch64' ]; then
	ARM64=1
elif [ "$MSYSTEM" ] && uname -a | grep -qi 'msys'; then
	MSYS2=1
fi

if [ "$MSYS2" ]; then
	DISTRO='MSYS2'
else
	DISTRO=$(grep '^ID=' '/etc/os-release' | cut -c 4-)
	[ "$DISTRO" ] || { echo 'Unable to determine distro.  Aborting'; exit 1; }
fi

cmdtest_py='test/cmdtest.py -n'
objtest_py='test/objtest.py'
objattrtest_py='test/objattrtest.py'
unit_tests_py='test/unit_tests.py --names --quiet'
tooltest_py='test/tooltest.py'
tooltest2_py='test/tooltest2.py --names --quiet'
gentest_py='test/gentest.py --quiet'
scrambletest_py='test/scrambletest.py'
altcoin_mod_opts='--quiet'
mmgen_tool='cmds/mmgen-tool'
pylint='PYTHONPATH=. pylint' # PYTHONPATH required by older Pythons (e.g. v3.9)
python='python3'
rounds=10

ORIG_ARGS=$@
PROGNAME=$(basename $0)

init_groups

while getopts hAbcdDfFLlNOps:StvV OPT
do
	case "$OPT" in
	h)  printf "  %-16s Test MMGen release\n" "${PROGNAME}:"
		echo   "  USAGE:           $PROGNAME [options] [tests or test group]"
		echo   "  OPTIONS: -h      Print this help message"
		echo   "           -A      Skip tests requiring altcoin modules or daemons"
		echo   "           -b      Buffer keypresses for all invocations of 'test/cmdtest.py'"
		echo   "           -c      Run tests in coverage mode"
		echo   "           -d      Enable Python Development Mode"
		echo   "           -D      Run tests in deterministic mode"
		echo   "           -f      Speed up the tests by using fewer rounds"
		echo   "           -F      Reduce rounds even further"
		echo   "           -L      List available tests and test groups with description"
		echo   "           -l      List the test name symbols"
		echo   "           -N      Pass the --no-timings switch to test/cmdtest.py"
		echo   "           -O      Use pexpect.spawn rather than popen_spawn where applicable"
		echo   "           -p      Pause between tests"
		echo   "           -s LIST Skip tests in LIST (space-separated)"
		echo   "           -S      Build sdist distribution, unpack, and run test"
		echo   "           -t      Print the tests without running them"
		echo   "           -v      Run test/cmdtest.py with '--exact-output' and other commands"
		echo   "                   with '--verbose' switch"
		echo   "           -V      Run test/cmdtest.py and other commands with '--verbose' switch"
		echo
		echo   "  For traceback output and error file support, set the EXEC_WRAPPER_TRACEBACK"
		echo   "  environment variable"
		exit ;;
	A)  SKIP_ALT_DEP=1
		cmdtest_py+=" --no-altcoin"
		unit_tests_py+=" --no-altcoin-deps"
		scrambletest_py+=" --no-altcoin"
		tooltest2_py+=" --no-altcoin" ;;
	b)  cmdtest_py+=" --buf-keypress" ;;
	c)  mkdir -p 'test/trace'
		touch 'test/trace.acc'
		cmdtest_py+=" --coverage"
		tooltest_py+=" --coverage"
		tooltest2_py+=" --fork --coverage"
		scrambletest_py+=" --coverage"
		python="python3 -m trace --count --file=test/trace.acc --coverdir=test/trace"
		unit_tests_py="$python $unit_tests_py"
		objtest_py="$python $objtest_py"
		objattrtest_py="$python $objattrtest_py"
		gentest_py="$python $gentest_py"
		mmgen_tool="$python $mmgen_tool" ;&
	d)  export PYTHONDEVMODE=1
		export PYTHONWARNINGS='error' ;;
	D)  export MMGEN_TEST_SUITE_DETERMINISTIC=1
		export MMGEN_DISABLE_COLOR=1 ;;
	f)  rounds=6 FAST=1 fast_opt='--fast' unit_tests_py+=" --fast" ;;
	F)  rounds=3 FAST=1 fast_opt='--fast' unit_tests_py+=" --fast" ;;
	L)  list_avail_tests; exit ;;
	l)  list_group_symbols; exit ;;
	N)  cmdtest_py+=" --no-timings" ;;
	O)  cmdtest_py+=" --pexpect-spawn" ;;
	p)  PAUSE=1 ;;
	s)  SKIP_LIST+=" $OPTARG" ;;
	S)  SDIST_TEST=1 ;;
	t)  LIST_CMDS=1 ;;
	v)  EXACT_OUTPUT=1 cmdtest_py+=" --exact-output" ;&
	V)  VERBOSE='--verbose'
		[ "$EXACT_OUTPUT" ] || cmdtest_py+=" --verbose"
		unit_tests_py="${unit_tests_py/--quiet/--verbose}"
		altcoin_mod_opts="${altcoin_mod_opts/--quiet/--verbose}"
		tooltest2_py="${tooltest2_py/--quiet/--verbose}"
		gentest_py="${gentest_py/--quiet/--verbose}"
		tooltest_py+=" --verbose"
		mmgen_tool+=" --verbose"
		objattrtest_py+=" --verbose"
		scrambletest_py+=" --verbose"
		pylint+=" --verbose" ;;
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

set -e

[ "$SDIST_TEST" -a -z "$TEST_RELEASE_IN_SDIST" ] && {
	test_dir='.sdist-test'
	rm -rf build dist *.egg-info $test_dir
	python3 -m build --no-isolation --sdist
	mkdir $test_dir
	tar -C $test_dir -axf dist/*.tar.gz
	cd $test_dir/mmgen-*
	python3 setup.py build_ext --inplace
	echo -e "\n${BLUE}Running 'test/test-release $ORIG_ARGS'$RESET $YELLOW[PWD=$PWD]$RESET\n"
	export TEST_RELEASE_IN_SDIST=1
	test/test-release.sh $ORIG_ARGS
	exit
}

case $1 in
	'')        tests=$dfl_tests ;;
	'default') tests=$dfl_tests ;;
	'extra')   tests=$extra_tests ;;
	'noalt')   tests=$noalt_tests
				SKIP_ALT_DEP=1
				cmdtest_py+=" --no-altcoin"
				unit_tests_py+=" --no-altcoin-deps"
				scrambletest_py+=" --no-altcoin" ;;
	'quick')   tests=$quick_tests ;;
	'qskip')   tests=$qskip_tests ;;
	*)         tests="$*" ;;
esac

rounds_min=$((rounds / 2))
for n in 2 5 10 20 50 100 200 500 1000; do
	eval "rounds${n}x=$((rounds*n))"
done

init_tests

remove_skipped_tests

check_tests

test/cmdtest.py clean

start_time=$(date +%s)

run_tests "$tests"

elapsed=$(($(date +%s)-start_time))
elapsed_fmt=$(printf %02d:%02d $((elapsed/60)) $((elapsed%60)))

[ "$LIST_CMDS" ] || {
	if [ "$MMGEN_TEST_SUITE_DETERMINISTIC" ]; then
		echo -e "\n${GREEN}All OK"
	else
		echo -e "\n${GREEN}All OK.  Total elapsed time: $elapsed_fmt$RESET"
	fi
}

#!/bin/bash
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

# Tested on Linux, Armbian, Raspbian, MSYS2

# data.sh must implement:
#   list_avail_tests()
#   init_groups()
#   init_tests()
. 'test/test-release.d/cfg.sh'

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

if [ "$(uname -m)" == 'armv7l' ]; then
	ARM32=1
elif [ "$(uname -m)" == 'aarch64' ]; then
	ARM64=1
elif uname -a | grep -q 'MSYS'; then
	MSYS2=1;
fi

if [ "$MSYS2" ]; then
	DISTRO='MSYS2'
else
	DISTRO=$(grep '^ID=' '/etc/os-release' | cut -c 4-)
	[ "$DISTRO" ] || { echo 'Unable to determine distro.  Aborting'; exit 1; }
fi

trap 'echo -e "${GREEN}Exiting at user request$RESET"; exit' INT

umask 0022

export MMGEN_TEST_SUITE=1
export MMGEN_NO_LICENSE=1
export PYTHONPATH=.

test_py='test/test.py -n'
objtest_py='test/objtest.py'
objattrtest_py='test/objattrtest.py'
unit_tests_py='test/unit_tests.py --names --quiet'
tooltest_py='test/tooltest.py'
tooltest2_py='test/tooltest2.py --names --quiet'
gentest_py='test/gentest.py --quiet'
scrambletest_py='test/scrambletest.py'
altcoin_mod_opts='--quiet'
mmgen_tool='cmds/mmgen-tool'
python='python3'

rounds=100 rounds_min=20 rounds_mid=250 rounds_max=500

ORIG_ARGS=$@
PROGNAME=$(basename $0)

init_groups

while getopts hAbCdDfFLlNOps:StvV OPT
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
		echo   "           -L      List available tests and test groups with description"
		echo   "           -l      List the test name symbols"
		echo   "           -N      Pass the --no-timings switch to test/test.py"
		echo   "           -O      Use pexpect.spawn rather than popen_spawn where applicable"
		echo   "           -p      Pause between tests"
		echo   "           -s LIST Skip tests in LIST (space-separated)"
		echo   "           -S      Build SDIST distribution, unpack, and run test"
		echo   "           -t      Print the tests without running them"
		echo   "           -v      Run test/test.py with '--exact-output' and other commands"
		echo   "                   with '--verbose' switch"
		echo   "           -V      Run test/test.py and other commands with '--verbose' switch"
		echo
		echo   "  For traceback output and error file support, set the EXEC_WRAPPER_TRACEBACK"
		echo   "  environment var"
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
		mmgen_tool="$python $mmgen_tool" ;&
	d)  export PYTHONDEVMODE=1
		export PYTHONWARNINGS='error' ;;
	D)  export MMGEN_TEST_SUITE_DETERMINISTIC=1
		export MMGEN_DISABLE_COLOR=1 ;;
	f)  FAST=1 rounds=10 rounds_min=3 rounds_mid=25 rounds_max=50 unit_tests_py+=" --fast" ;;
	F)  FAST=1 rounds=3 rounds_min=1 rounds_mid=3 rounds_max=5 unit_tests_py+=" --fast" ;;
	L)  list_avail_tests; exit ;;
	l)  list_group_symbols; exit ;;
	N)  test_py+=" --no-timings" ;;
	O)  test_py+=" --pexpect-spawn" ;;
	p)  PAUSE=1 ;;
	s)  SKIP_LIST+=" $OPTARG" ;;
	S)  SDIST_TEST=1 ;;
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

[ "$SDIST_TEST" -a -z "$MMGEN_TEST_RELEASE_IN_SDIST" ] && {
	test_dir='.sdist-test'
	rm -rf build dist MMGen.egg-info $test_dir
	python3 -m build --no-isolation --sdist
	mkdir $test_dir
	tar -C $test_dir -axf dist/*.tar.gz
	cd $test_dir/MMGen-*
	python3 setup.py build_ext --inplace
	echo -e "\n${BLUE}Running 'test/test-release $ORIG_ARGS'$RESET $YELLOW[PWD=$PWD]$RESET\n"
	export MMGEN_TEST_RELEASE_IN_SDIST=1
	test/test-release.sh $ORIG_ARGS
	exit
}

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

set -e

init_tests

remove_skipped_tests

check_tests

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

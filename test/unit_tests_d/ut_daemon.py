#!/usr/bin/env python3
"""
test/unit_tests_d/ut_daemon.py: unit test for the MMGen suite's Daemon class
"""

from subprocess import run,DEVNULL
from mmgen.common import *
from mmgen.exception import *
from mmgen.daemon import *
from mmgen.protocol import init_proto

def test_flags():
	d = CoinDaemon('eth')
	vmsg(f'Available opts:  {fmt_list(d.avail_opts,fmt="bare")}')
	vmsg(f'Available flags: {fmt_list(d.avail_flags,fmt="bare")}')
	vals = namedtuple('vals',['online','no_daemonize','keep_cfg_file'])

	def gen():
		for opts,flags,val in (
				(None,None,                                   vals(False,False,False)),
				(None,['keep_cfg_file'],                      vals(False,False,True)),
				(['online'],['keep_cfg_file'],                vals(True,False,True)),
				(['online','no_daemonize'],['keep_cfg_file'], vals(True,True,True)),
			):
			d = CoinDaemon('eth',opts=opts,flags=flags)
			assert d.flag.keep_cfg_file == val.keep_cfg_file
			assert d.opt.online == val.online
			assert d.opt.no_daemonize == val.no_daemonize
			d.flag.keep_cfg_file = not val.keep_cfg_file
			d.flag.keep_cfg_file = val.keep_cfg_file
			yield d

	return tuple(gen())

def test_flags_err(ut,d):

	def bad1(): d[0].flag.foo = False
	def bad2(): d[0].opt.foo = False
	def bad3(): d[0].opt.no_daemonize = True
	def bad4(): d[0].flag.keep_cfg_file = 'x'
	def bad5(): d[0].opt.no_daemonize = 'x'
	def bad6(): d[0].flag.keep_cfg_file = False
	def bad7(): d[1].flag.keep_cfg_file = True

	ut.process_bad_data((
		('flag (1)', 'ClassFlagsError', 'unrecognized flag', bad1 ),
		('opt  (1)', 'ClassFlagsError', 'unrecognized opt',  bad2 ),
		('opt  (2)', 'AttributeError',  'is read-only',      bad3 ),
		('flag (2)', 'AssertionError',  'not boolean',       bad4 ),
		('opt  (3)', 'AttributeError',  'is read-only',      bad5 ),
		('flag (3)', 'ClassFlagsError', 'not set',           bad6 ),
		('flag (4)', 'ClassFlagsError', 'already set',       bad7 ),
	))

def test_cmds(op):
	network_ids = CoinDaemon.get_network_ids()
	for test_suite in [True,False] if op == 'print' else [True]:
		vmsg(orange(f'Start commands (op={op}, test_suite={test_suite}):'))
		for coin,data in CoinDaemon.coins.items():
			for daemon_id in data.daemon_ids:
				for network in globals()[daemon_id+'_daemon'].networks:
					if opt.no_altcoin_deps and coin != 'BTC':
						continue
					d = CoinDaemon(
						proto=init_proto(coin=coin,network=network),
						daemon_id = daemon_id,
						test_suite = test_suite )
					if op == 'print':
						for cmd in d.start_cmds:
							vmsg(' '.join(cmd))
					elif op == 'check':
						try:
							cp = run([d.exec_fn,'--help'],stdout=PIPE,stderr=PIPE)
						except:
							ydie(1,f'Unable to execute {d.exec_fn}')
						if cp.returncode:
							ydie(1,f'Unable to execute {d.exec_fn}')
						else:
							vmsg('{:16} {}'.format(
								d.exec_fn+':',
								cp.stdout.decode().splitlines()[0] ))
					else:
						if opt.quiet:
							msg_r('.')
						getattr(d,op)(silent=opt.quiet)

class unit_tests:

	def flags(self,name,ut):

		qmsg_r('Testing flags and opts...')
		vmsg('')
		daemons = test_flags()
		qmsg('OK')

		qmsg_r('Testing error handling for flags and opts...')
		vmsg('')
		test_flags_err(ut,daemons)
		qmsg('OK')

		return True

	def cmds(self,name,ut):
		qmsg_r('Testing start commands for coin daemons...')
		vmsg('')
		test_cmds('print')
		qmsg('OK')
		return True

	def exec(self,name,ut):
		qmsg_r('Testing availability of coin daemons...')
		vmsg('')
		test_cmds('check')
		qmsg('OK')
		return True

	def start(self,name,ut):
		msg_r('Starting coin daemons...')
		qmsg('')
		test_cmds('start')
		msg('OK')
		return True

	def stop(self,name,ut):
		msg_r('Stopping coin daemons...')
		qmsg('')
		test_cmds('stop')
		msg('OK')
		return True

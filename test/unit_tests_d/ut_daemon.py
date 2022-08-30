#!/usr/bin/env python3
"""
test/unit_tests_d/ut_daemon.py: unit test for the MMGen suite's Daemon class
"""

from subprocess import run,DEVNULL
from mmgen.common import *
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

def test_cmd(args_in,message):
	qmsg_r(message)
	args = ['python3', f'test/{args_in[0]}-coin-daemons.py'] + list(args_in[1:])
	vmsg('\n' + orange(f"Running '{' '.join(args)}':"))
	pipe = None if opt.verbose else PIPE
	cp = run( args, stdout=pipe, stderr=pipe, check=True )
	qmsg('OK')
	return True

class unit_tests:

	win_skip = ('start','status','stop')

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

	def exec(self,name,ut):
		return test_cmd(['start','-Vm','all'], 'Testing availability of coin daemons...')

	def cmds(self,name,ut):
		return test_cmd(['start','-t','all'], 'Testing start commands for coin daemons...')

	def start(self,name,ut):
		return test_cmd(['start','all'], 'Starting coin daemons...')

	def status(self,name,ut):
		return test_cmd(['start','all'], 'Checking status of coin daemons...')

	def stop(self,name,ut):
		return test_cmd(['stop','all'], 'Stopping coin daemons...')

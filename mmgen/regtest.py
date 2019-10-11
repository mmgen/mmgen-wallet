#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
regtest: Coin daemon regression test mode setup and operations for the MMGen suite
"""

import os,subprocess,time,shutil
from mmgen.common import *
PIPE = subprocess.PIPE

data_dir     = os.path.join(g.data_dir_root,'regtest',g.coin.lower())
daemon_dir   = os.path.join(data_dir,'regtest')
rpc_ports    = { 'btc':8552, 'bch':8553, 'b2x':8554, 'ltc':8555 }
rpc_port     = rpc_ports[g.coin.lower()]
rpc_user     = 'bobandalice'
rpc_password = 'hodltothemoon'

tr_wallet = lambda user: os.path.join(daemon_dir,'wallet.dat.'+user)

common_args = lambda: (
	'--rpcuser={}'.format(rpc_user),
	'--rpcpassword={}'.format(rpc_password),
	'--rpcport={}'.format(rpc_port),
	'--regtest',
	'--datadir={}'.format(data_dir))

def start_daemon(user,quiet=False,daemon=True,reindex=False):
	# requires Bitcoin ABC version >= 0.16.2
	add_args = ()
	if g.proto.daemon_name == 'bitcoind-abc': add_args = ('--usecashaddr=0',)
	elif g.proto.daemon_name == 'litecoind':  add_args = ('--mempoolreplacement=1',)
	cmd = (
		g.proto.daemon_name,
		'--listen=0',
		'--keypool=1',
		'--wallet={}'.format(os.path.basename(tr_wallet(user)))
	) + add_args + common_args()
	if daemon: cmd += ('--daemon',)
	if reindex: cmd += ('--reindex',)
	if not g.debug or quiet: vmsg('{}'.format(' '.join(cmd)))
	p = subprocess.Popen(cmd,stdout=PIPE,stderr=PIPE)
	err = process_output(p,silent=False)[1]
	if err:
		rdie(1,'Error starting the {} daemon:\n{}'.format(g.proto.name.capitalize(),err))

def start_daemon_mswin(user,quiet=False,reindex=False):
	import threading
	t = threading.Thread(target=start_daemon,args=[user,quiet,False,reindex])
	t.daemon = True
	t.start()
	if not opt.verbose: Msg_r(' \b') # blocks w/o this...crazy

def start_cmd(*args,**kwargs):
	cmd = args
	if args[0] == 'cli':
		cmd = (g.proto.name+'-cli',) + common_args() + args[1:]
	if g.debug or not 'quiet' in kwargs:
		vmsg('{}'.format(' '.join(cmd)))
	ip = op = ep = (PIPE,None)['no_pipe' in kwargs and kwargs['no_pipe']]
	if 'pipe_stdout_only' in kwargs and kwargs['pipe_stdout_only']: ip = ep = None
	return subprocess.Popen(cmd,stdin=ip,stdout=op,stderr=ep)

def test_daemon():
	p = start_cmd('cli','getblockcount',quiet=True)
	err = process_output(p,silent=True)[1]
	ret,state = p.wait(),None
	if "error: couldn't connect" in err or "error: Could not connect" in err:
		state = 'stopped'
	if not state: state = ('busy','ready')[ret==0]
	return state

def wait_for_daemon(state,silent=False,nonl=False):
	for i in range(200):
		ret = test_daemon()
		if not silent:
			if opt.verbose: msg('returning state '+ret)
			else: gmsg_r('.')
			if ret == state and not nonl: msg('')
		if ret == state: return True
		time.sleep(1)
	else:
		die(1,'timeout exceeded')

def get_balances():
	user1 = get_current_user(quiet=True)
	if user1 == None:
		user('bob')
		user1 = get_current_user(quiet=True)
#		die(1,'Regtest daemon not running')
	user2 = ('bob','alice')[user1=='bob']
	tbal = 0
	# don't need to save and restore these, as we exit immediately
	g.rpc_host = 'localhost'
	g.rpc_port = rpc_port
	g.rpc_user = rpc_user
	g.rpc_password = rpc_password
	g.testnet = True
	rpc_init()
	for u in (user1,user2):
		bal = g.proto.coin_amt(g.rpch.getbalance('*',0,True))
		if u == user1: user(user2)
		msg('{:<16} {:12}'.format(u.capitalize()+"'s balance:",bal))
		tbal += bal
	msg('{:<16} {:12}'.format('Total balance:',tbal))

def create_data_dir():
	try: os.stat(os.path.join(data_dir,'regtest')) # don't use daemon_dir, as data_dir may change
	except: pass
	else:
		m = "Delete your existing MMGen regtest setup at '{}' and create a new one?"
		if keypress_confirm(m.format(data_dir)):
			shutil.rmtree(data_dir)
		else:
			die()

	try: os.makedirs(data_dir)
	except: pass

def process_output(p,silent=False):
	out = p.stdout.read().decode()
	if g.platform == 'win' and not opt.verbose: Msg_r(' \b')
	err = p.stderr.read().decode()
	if g.debug or not silent:
		vmsg('stdout: [{}]'.format(out.strip()))
		vmsg('stderr: [{}]'.format(err.strip()))
	return out,err

def start_and_wait(user,silent=False,nonl=False,reindex=False):
	vmsg('Starting {} regtest daemon'.format(g.proto.name))
	(start_daemon_mswin,start_daemon)[g.platform=='linux'](user,reindex=reindex)
	wait_for_daemon('ready',silent=silent,nonl=nonl)

def stop_and_wait(silent=False,nonl=False,stop_silent=False,ignore_noconnect_error=False):
	stop(silent=stop_silent,ignore_noconnect_error=ignore_noconnect_error)
	wait_for_daemon('stopped',silent=silent,nonl=nonl)

def send(addr,amt):
	user('miner')
	gmsg('Sending {} {} to address {}'.format(amt,g.coin,addr))
	p = start_cmd('cli','sendtoaddress',addr,str(amt))
	process_output(p)
	p.wait()
	generate(1)

def show_mempool():
	p = start_cmd('cli','getrawmempool')
	from ast import literal_eval
	msg(mmgen_pformat(literal_eval(p.stdout.read().decode())))
	p.wait()

def cli(*args):
	p = start_cmd(*(('cli',) + args))
	Msg_r(p.stdout.read().decode())
	msg_r(p.stderr.read().decode())
	p.wait()

def fork(coin):
	coin = coin.upper()
	from mmgen.protocol import CoinProtocol
	forks = CoinProtocol(coin,False).forks
	if not [f for f in forks if f[2] == g.coin.lower() and f[3] == True]:
		die(1,"Coin {} is not a replayable fork of coin {}".format(g.coin,coin))

	gmsg('Creating fork from coin {} to coin {}'.format(coin,g.coin))
	source_data_dir = os.path.join(g.data_dir_root,'regtest',coin.lower())

	try: os.stat(source_data_dir)
	except: die(1,"Source directory '{}' does not exist!".format(source_data_dir))

	# stop the other daemon
	global rpc_port,data_dir
	rpc_port_save,data_dir_save = rpc_port,data_dir
	rpc_port = rpc_ports[coin.lower()]
	data_dir = os.path.join(g.data_dir_root,'regtest',coin.lower())
	if test_daemon() != 'stopped':
		stop_and_wait(silent=True,stop_silent=True)
	rpc_port,data_dir = rpc_port_save,data_dir_save

	try: os.makedirs(data_dir)
	except: pass

	# stop our daemon
	if test_daemon() != 'stopped':
		stop_and_wait(silent=True,stop_silent=True)

	create_data_dir()
	os.rmdir(data_dir)
	shutil.copytree(source_data_dir,data_dir,symlinks=True)
	start_and_wait('miner',reindex=True,silent=True)
	stop_and_wait(silent=True,stop_silent=True)
	gmsg('Fork {} successfully created'.format(g.coin))

def setup():
	try: os.makedirs(data_dir)
	except: pass

	if test_daemon() != 'stopped':
		stop_and_wait(silent=True,stop_silent=True)
	create_data_dir()

	gmsg('Starting setup')

	gmsg_r('Creating miner wallet')
	start_and_wait('miner')
	generate(432,silent=True)
	stop_and_wait(silent=True,stop_silent=True)

	for user in ('alice','bob'):
		gmsg_r("Creating {}'s tracking wallet".format(user.capitalize()))
		start_and_wait(user)
		if user == 'bob' and opt.setup_no_stop_daemon:
			msg('Leaving daemon running with Bob as current user')
		else:
			stop_and_wait(silent=True,stop_silent=True)

	gmsg('Setup complete')

def get_current_user_win(quiet=False):
	if test_daemon() == 'stopped': return None
	logfile = os.path.join(daemon_dir,'debug.log')
	for ss in ('Wallet completed loading in','Using wallet wallet'):
		o = start_cmd('grep',ss,logfile,quiet=True).stdout.readlines()
		if o:
			last_line = o[-1].decode()
			break
	else:
		rdie(2,"Unable to find user info in 'debug.log'")

	import re
	m = re.search(r'\bwallet\.dat\.([a-z]+)',last_line)
	if not m:
		return None

	user = m.group(1)
	if user in ('miner','bob','alice'):
		if not quiet:
			msg('Current user is {}'.format(user.capitalize()))
		return user
	else:
		return None

def get_current_user_unix(quiet=False):
	p = start_cmd('pgrep','-af','{}.*--rpcport={}.*'.format(g.proto.daemon_name,rpc_port),quiet=True)
	cmdline = p.stdout.read().decode()
	if not cmdline: return None
	for k in ('miner','bob','alice'):
		if 'wallet.dat.'+k in cmdline:
			if not quiet: msg('Current user is {}'.format(k.capitalize()))
			return k
	return None

get_current_user = { 'win':get_current_user_win, 'linux':get_current_user_unix }[g.platform]

def bob():   return user('bob',quiet=False)
def alice(): return user('alice',quiet=False)
def miner(): return user('miner',quiet=False)
def user(user=None,quiet=False):
	if user==None:
		get_current_user()
		return True
	if test_daemon() == 'busy':
		wait_for_daemon('ready')
	if test_daemon() == 'ready':
		if user == get_current_user(quiet=True):
			if not quiet: msg('{} is already the current user for coin {}'.format(user.capitalize(),g.coin))
			return True
		gmsg_r('Switching to user {} for coin {}'.format(user.capitalize(),g.coin))
		stop_and_wait(silent=False,nonl=True,stop_silent=True)
		time.sleep(0.1) # file lock has race condition - TODO: test for lock file
		start_and_wait(user,nonl=True)
	else:
		gmsg_r('Starting regtest daemon for coin {} with current user {}'.format(g.coin,user.capitalize()))
		start_and_wait(user,nonl=True)
	gmsg('done')

def stop(silent=False,ignore_noconnect_error=True):
	if test_daemon() != 'stopped' and not silent:
		gmsg('Stopping {} regtest daemon for coin {}'.format(g.proto.name,g.coin))
	p = start_cmd('cli','stop')
	err = process_output(p)[1]
	if err:
		if "couldn't connect to server" in err and not ignore_noconnect_error:
			rdie(1,'Error stopping the {} daemon:\n{}'.format(g.proto.name.capitalize(),err))
		msg(err)
	return p.wait()

def generate(blocks=1,silent=False):

	def have_generatetoaddress():
		p = start_cmd('cli','help','generatetoaddress')
		out,err = process_output(p,silent=True)
		return not 'unknown command' in out

	def get_miner_address():
		p = start_cmd('cli','getnewaddress')
		out,err = process_output(p,silent=True)
		if not err:
			return out.strip()
		else:
			rdie(1,'Error getting new address:\n{}'.format(err))

	if test_daemon() == 'stopped':
		die(1,'Regtest daemon is not running')

	wait_for_daemon('ready',silent=True)

	if have_generatetoaddress():
		p = start_cmd('cli','generatetoaddress',str(blocks),get_miner_address())
	else:
		p = start_cmd('cli','generate',str(blocks))

	out,err = process_output(p,silent=silent)

	from ast import literal_eval
	if not out or len(literal_eval(out)) != blocks:
		rdie(1,'Error generating blocks')
	p.wait()
	gmsg('Mined {} block{}'.format(blocks,suf(blocks)))

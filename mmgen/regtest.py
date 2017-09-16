#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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
regtest: Bitcoind regression test mode setup and operations for the MMGen suite
"""

import os,subprocess,time,shutil
from mmgen.common import *

data_dir = os.path.join(g.data_dir,'regtest')
regtest_dir = os.path.join(data_dir,'regtest')
rpc_port = 8552
rpc_user = 'bobandalice'
rpc_password = 'hodltothemoon'
init_amt = 500
tr_wallet = {
	'orig':  os.path.join(regtest_dir,'wallet.dat.orig'),
	'bob':   os.path.join(regtest_dir,'wallet.dat.bob'),
	'alice': os.path.join(regtest_dir,'wallet.dat.alice')
}
mmwords = {
	'bob':   os.path.join(data_dir,'1163DDF1[128].mmwords'),
	'alice': os.path.join(data_dir,'9304C211[128].mmwords')
}
mmaddrs = {
	'bob':   os.path.join(data_dir,'1163DDF1{}[1-10].addrs'),
	'alice': os.path.join(data_dir,'9304C211{}[1-10].addrs')
}
mnemonic = {
	'bob':   'ignore bubble ignore crash stay long stay patient await glorious destination moon',
	'alice': 'stay long guard secret await price rise destination moon enjoy rich future'
}
send_addr = {
	'bob':   'mw42oJ94yRA6ZUNSzmMpjZDR74JNyvqzzZ',
	'alice': '2N3HhxasbRvrJyHg72JNVCCPi9EUGrEbFnu',
}

common_args = (
	'-rpcuser={}'.format(rpc_user),
	'-rpcpassword={}'.format(rpc_password),
	'-regtest',
	'-datadir={}'.format(data_dir))

def start_daemon(user,quiet=False,daemon=True):
	cmd = (
		'bitcoind',
		'-keypool=1',
		'-rpcbind=localhost:{}'.format(rpc_port),
		'-rpcallowip=::1',
		'-wallet={}'.format(os.path.basename(tr_wallet[user]))
	) + common_args
	if daemon: cmd += ('-daemon',)
	if not g.debug or quiet: vmsg('{}'.format(' '.join(cmd)))
	p = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	err = process_output(p,silent=False)[1]
	if err:
		rdie(1,'Error starting the Bitcoin daemon:\n{}'.format(err))

def start_daemon_mswin(user,quiet=False):
	import threading
	t = threading.Thread(target=start_daemon,args=[user,quiet,False])
	t.daemon = True
	t.start()
	if not opt.verbose: Msg_r(' \b') # blocks w/o this...crazy

def start_cmd(*args,**kwargs):
	cmd = args
	if args[0] == 'cli':
		cmd = ('bitcoin-cli','-rpcconnect=localhost','-rpcport={}'.format(rpc_port)) + common_args + args[1:]
	if g.debug or not 'quiet' in kwargs:
		vmsg('{}'.format(' '.join(cmd)))
	return subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def test_daemon():
	p = start_cmd('cli','getblockcount',quiet=True)
	err = process_output(p,silent=True)[1]
	ret,state = p.wait(),None
	if "error: couldn't connect" in err: state = 'stopped'
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
	user2 = ('bob','alice')[user1=='bob']
	tbal = 0
	from mmgen.obj import BTCAmt
	for user in (user1,user2):
		p = start_cmd('python','mmgen-tool','--{}'.format(user),'getbalance','quiet=1')
		bal = BTCAmt(p.stdout.read())
		ustr = "{}'s balance:".format(user.capitalize())
		msg('{:<16} {:12}'.format(ustr,bal))
		tbal += bal
	msg('{:<16} {:12}'.format('Total balance:',tbal))
	msg('{:<16} {:12}'.format('Miner fees:',1000-tbal))

def create_data_dir():
#def keypress_confirm(prompt,default_yes=False,verbose=False,no_nl=False):
	try: os.stat(regtest_dir)
	except: pass
	else:
		if keypress_confirm('Delete your existing MMGen regtest setup and create a new one?'):
			shutil.rmtree(data_dir)
		else:
			die()

	try: os.mkdir(data_dir)
	except: pass

def process_output(p,silent=False):
	out = p.stdout.read()
	err = p.stderr.read()
	if g.debug or not silent:
		vmsg('stdout: [{}]'.format(out.strip()))
		vmsg('stderr: [{}]'.format(err.strip()))
	return out,err

def create_mmgen_wallet(user):
	gmsg("Creating {}'s MMGen wallet".format(user.capitalize()))
	p = start_cmd('python','mmgen-walletconv','-d',data_dir,'-i','words','-o','words')
	p.stdin.write(mnemonic[user]+'\n')
	p.stdin.close()
	err = process_output(p)[1]
	if not 'written to file' in err:
		rdie(1,'Error creating MMGen wallet')
	p.wait()

def create_mmgen_addrs(user,addr_type):
	gmsg('Creating MMGen addresses for user {} (type: {})'.format(user.capitalize(),addr_type))
	suf = ('-'+addr_type,'')[addr_type=='L']
	try: os.unlink(mmaddrs[user].format(suf))
	except: pass
	p = start_cmd('python','mmgen-addrgen','--{}'.format(user),'-d',data_dir,'--type',addr_type,mmwords[user],'1-10')
	p.stdin.write(mnemonic[user]+'\n')
	p.stdin.close()
	err = process_output(p)[1]
	if not 'written to file' in err:
		rdie(1,'Error creating MMGen addresses')
	p.wait()

def import_mmgen_addrs(user,addr_type):
	gmsg_r('Importing MMGen addresses for user {} (type: {})'.format(user.capitalize(),addr_type))
	suf = ('-'+addr_type,'')[addr_type=='L']
	p = start_cmd('python','mmgen-addrimport','--{}'.format(user),'-q','--batch',mmaddrs[user].format(suf))
	p.stdin.write(mnemonic[user]+'\n')
	p.stdin.close()
	err = process_output(p)[1]
	if not 'addresses imported' in err:
		rdie(1,'Error importing MMGen addresses')
	p.wait()

def start_and_wait(user,silent=False,nonl=False):
	vmsg('Starting bitcoin regtest daemon')
	(start_daemon_mswin,start_daemon)[g.platform=='linux'](user)
	wait_for_daemon('ready',silent=silent,nonl=nonl)

def stop_and_wait(silent=False,nonl=False,stop_silent=False,ignore_noconnect_error=False):
	stop(silent=stop_silent,ignore_noconnect_error=ignore_noconnect_error)
	wait_for_daemon('stopped',silent=silent,nonl=nonl)

def setup_wallet(user,addr_type):
	gmsg_r("Setting up {}'s tracking wallet".format(user.capitalize()))
	start_and_wait(user)
	create_mmgen_wallet(user)
	create_mmgen_addrs(user,addr_type)
	import_mmgen_addrs(user,addr_type)
	stop_and_wait(stop_silent=True)

def setup_mixed_wallet(user):
	gmsg_r("Setting up {}'s wallet (mixed address types)".format(user.capitalize()))
	start_and_wait(user)
	create_mmgen_wallet(user)
	create_mmgen_addrs(user,'L')
	create_mmgen_addrs(user,'C')
	create_mmgen_addrs(user,'S')
	import_mmgen_addrs(user,'L'); msg('')
	import_mmgen_addrs(user,'C'); msg('')
	import_mmgen_addrs(user,'S'); msg('')
	stop_and_wait(silent=True,stop_silent=True)

def fund_wallet(user,amt):
	gmsg('Sending {} BTC to {}'.format(amt,user.capitalize()))
	p = start_cmd('cli','sendtoaddress',send_addr[user],str(amt))
	process_output(p)
	p.wait()

def setup():
	try: os.mkdir(data_dir)
	except: pass
	if test_daemon() != 'stopped':
		stop_and_wait(silent=True,stop_silent=True)
	create_data_dir()
	gmsg_r('Starting setup')

	start_and_wait('orig')

	generate(432,silent=True)

	stop_and_wait(silent=True,stop_silent=True)

	if opt.mixed:
		setup_mixed_wallet('bob')
		setup_mixed_wallet('alice')
	else:
		setup_wallet('bob','C')
		setup_wallet('alice','S')

	if opt.empty:
		msg("'--empty' selected: skipping funding of wallets")
	else:
		start_and_wait('orig',silent=True)
		fund_wallet('bob',init_amt)
		fund_wallet('alice',init_amt)
		generate(1)
		stop_and_wait(silent=True,stop_silent=True)

	gmsg('Setup complete')

def get_current_user_win(quiet=False):
	if test_daemon() == 'stopped': return None
	p = start_cmd('grep','Using wallet',os.path.join(regtest_dir,'debug.log'))
	try: wallet_fn = p.stdout.readlines()[-1].split()[-1]
	except: return None
	for k in ('orig','bob','alice'):
		if wallet_fn == 'wallet.dat.'+k:
			if not quiet: msg('Current user is {}'.format(k.capitalize()))
			return k
	return None

def get_current_user_unix(quiet=False):
	p = start_cmd('pgrep','-af', 'bitcoind.*-rpcuser={}.*'.format(rpc_user))
	cmdline = p.stdout.read()
	if not cmdline: return None
	for k in ('orig','bob','alice'):
		if 'wallet.dat.'+k in cmdline:
			if not quiet: msg('Current user is {}'.format(k.capitalize()))
			return k
	return None

get_current_user = (get_current_user_win,get_current_user_unix)[g.platform=='linux']

def bob():   return user('bob',quiet=False)
def alice(): return user('alice',quiet=False)
def user(user=None,quiet=False):
	if user==None:
		get_current_user()
		return True
	if test_daemon() == 'busy':
		wait_for_daemon('ready')
	if test_daemon() == 'ready':
		if user == get_current_user(quiet=True):
			if not quiet: msg('{} is already the current user'.format(user.capitalize()))
			return True
		gmsg_r('Switching to user {}'.format(user.capitalize()))
		stop_and_wait(silent=False,nonl=True,stop_silent=True)
		start_and_wait(user,silent=False,nonl=True)
	else:
		gmsg_r('Starting regtest daemon with current user {}'.format(user.capitalize()))
		start_and_wait(user,silent=False,nonl=True)
	gmsg('done')

def stop(silent=False,ignore_noconnect_error=True):
	if test_daemon() != 'stopped' and not silent:
		gmsg('Stopping bitcoin regtest daemon')
	p = start_cmd('cli','stop')
	err = process_output(p)[1]
	if err:
		if "couldn't connect to server" in err and not ignore_noconnect_error:
			rdie(1,'Error stopping the Bitcoin daemon:\n{}'.format(err))
		msg(err)
	return p.wait()

def generate(blocks=1,silent=False):
	if test_daemon() == 'stopped':
		die(1,'Regtest daemon is not running')
	wait_for_daemon('ready',silent=True)
	p = start_cmd('cli','generate',str(blocks))
	out = process_output(p,silent=silent)[0]
	if len(eval(out)) != blocks:
		rdie(1,'Error generating blocks')
	p.wait()
	gmsg('Mined {} block{}'.format(blocks,suf(blocks,'s')))

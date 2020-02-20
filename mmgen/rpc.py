#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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
rpc.py:  Cryptocoin RPC library for the MMGen suite
"""

import http.client,base64,json
from decimal import Decimal

from mmgen.common import *

def dmsg_rpc(fs,data=None,is_json=False):
	if g.debug_rpc:
		msg(fs if data == None else fs.format(pp_fmt(json.loads(data) if is_json else data)))

class RPCConnection(MMGenObject):

	auth = True
	db_fs = '    host [{h}] port [{p}] user [{u}] passwd [{pw}] auth_cookie [{c}]\n'
	http_hdrs = { 'Content-Type': 'application/json' }

	def __init__(self,host=None,port=None,user=None,passwd=None,auth_cookie=None,socket_timeout=1):

		dmsg_rpc('=== {}.__init__() debug ==='.format(type(self).__name__))
		dmsg_rpc(self.db_fs.format(h=host,p=port,u=user,pw=passwd,c=auth_cookie))

		import socket
		try:
			socket.create_connection((host,port),timeout=socket_timeout).close()
		except:
			raise SocketError('Unable to connect to {}:{}'.format(host,port))

		if not self.auth:
			pass
		elif user and passwd:
			self.auth_str = '{}:{}'.format(user,passwd)
		elif auth_cookie:
			self.auth_str = auth_cookie
		else:
			msg('Error: no {} RPC authentication method found'.format(g.proto.name.capitalize()))
			if passwd: die(1,"'rpcuser' entry not found in {}.conf or mmgen.cfg".format(g.proto.name))
			elif user: die(1,"'rpcpassword' entry not found in {}.conf or mmgen.cfg".format(g.proto.name))
			else:
				m1 = 'Either provide rpcuser/rpcpassword in {pn}.conf or mmgen.cfg\n'
				m2 = '(or, alternatively, copy the authentication cookie to the {pnu}\n'
				m3 = 'data dir if {pnm} and {dn} are running as different users)'
				die(1,(m1+m2+m3).format(
					pn=g.proto.name,
					pnu=g.proto.name.capitalize(),
					dn=g.proto.daemon_name,
					pnm=g.proj_name))

		if self.auth:
			fs = '    RPC AUTHORIZATION data ==> raw: [{}]\n{:>31}enc: [Basic {}]\n'
			as_enc = base64.b64encode(self.auth_str.encode()).decode()
			dmsg_rpc(fs.format(self.auth_str,'',as_enc))
			self.http_hdrs.update({ 'Host':host, 'Authorization':'Basic {}'.format(as_enc) })

		self.host = host
		self.port = port

		for method in self.rpcmethods:
			exec('{c}.{m} = lambda self,*args,**kwargs: self.request("{m}",*args,**kwargs)'.format(
						c=type(self).__name__,m=method))

	# Normal mode: call with arg list unrolled, exactly as with cli
	# Batch mode:  call with list of arg lists as first argument
	# kwargs are for local use and are not passed to server

	# By default, raises RPCFailure exception with an error msg on all errors and exceptions
	# on_fail is one of 'raise' (default), 'return' or 'silent'
	# With on_fail='return', returns 'rpcfail',(resp_object,(die_args))
	def request(self,cmd,*args,**kwargs):

		if g.debug:
			print_stack_trace('RPC REQUEST {}\n  args: {!r}\n  kwargs: {!r}'.format(cmd,args,kwargs))

		if g.rpc_fail_on_command == cmd:
			cmd = 'badcommand_' + cmd

		cf = { 'timeout':g.http_timeout, 'batch':False, 'on_fail':'raise' }

		if cf['on_fail'] not in ('raise','return','silent'):
			raise ValueError("request(): {}: illegal value for 'on_fail'".format(cf['on_fail']))

		for k in cf:
			if k in kwargs and kwargs[k]: cf[k] = kwargs[k]

		if cf['batch']:
			p = [{'method':cmd,'params':r,'id':n,'jsonrpc':'2.0'} for n,r in enumerate(args[0],1)]
		else:
			p = {'method':cmd,'params':args,'id':1,'jsonrpc':'2.0'}

		dmsg_rpc('=== request() debug ===')
		dmsg_rpc('    RPC POST data ==>\n{}\n',p)

		ca_type = self.coin_amt_type if hasattr(self,'coin_amt_type') else str
		from mmgen.obj import HexStr
		class MyJSONEncoder(json.JSONEncoder):
			def default(self,obj):
				if isinstance(obj,g.proto.coin_amt):
					return ca_type(obj)
				elif isinstance(obj,HexStr):
					return obj
				else:
					return json.JSONEncoder.default(self,obj)

		data = json.dumps(p,cls=MyJSONEncoder)

		def do_fail(*args): # args[0] is either None or HTTPResponse object
			if cf['on_fail'] in ('return','silent'): return 'rpcfail',args

			try:    s = '{}'.format(args[2])
			except: s = repr(args[2])

			if s == '' and args[0] != None:
				from http import HTTPStatus
				hs = HTTPStatus(args[0].code)
				s = '{} {}'.format(hs.value,hs.name)

			raise RPCFailure(s)

		hc = http.client.HTTPConnection(self.host,self.port,cf['timeout'])
		try:
			hc.request('POST','/',data,self.http_hdrs)
		except Exception as e:
			m = '{}\nUnable to connect to {} at {}:{}'
			return do_fail(None,2,m.format(e.args[0],g.proto.daemon_name,self.host,self.port))

		try:
			r = hc.getresponse() # returns HTTPResponse instance
		except Exception:
			m = 'Unable to connect to {} at {}:{} (but port is bound?)'
			return do_fail(None,2,m.format(g.proto.daemon_name,self.host,self.port))

		dmsg_rpc('    RPC GETRESPONSE data ==>\n{}\n',r.__dict__)

		if r.status != 200:
			if cf['on_fail'] not in ('silent','raise'):
				msg_r(yellow('{} RPC Error: '.format(g.proto.daemon_name.capitalize())))
				msg(red('{} {}'.format(r.status,r.reason)))
			e1 = r.read().decode()
			try:
				e3 = json.loads(e1)['error']
				e2 = '{} (code {})'.format(e3['message'],e3['code'])
			except:
				e2 = str(e1)
			return do_fail(r,1,e2)

		r2 = r.read().decode()

		dmsg_rpc('    RPC REPLY data ==>\n{}\n',r2,is_json=True)

		if not r2:
			return do_fail(r,2,'Empty reply')

		r3 = json.loads(r2,parse_float=Decimal)
		ret = []

		for resp in r3 if cf['batch'] else [r3]:
			if 'error' in resp and resp['error'] != None:
				return do_fail(r,1,'{} returned an error: {}'.format(
					g.proto.daemon_name.capitalize(),resp['error']))
			elif 'result' not in resp:
				return do_fail(r,1, 'Missing JSON-RPC result\n' + repr(resps))
			else:
				ret.append(resp['result'])

		return ret if cf['batch'] else ret[0]

	rpcmethods = (
		'backupwallet',
		'createrawtransaction',
		'decoderawtransaction',
		'disconnectnode',
		'estimatefee',
		'estimatesmartfee',
		'getaddressesbyaccount',
		'getaddressesbylabel',
		'getblock',
		'getblockchaininfo',
		'getblockcount',
		'getblockhash',
		'getmempoolinfo',
		'getmempoolentry',
		'getnettotals',
		'getnetworkinfo',
		'getpeerinfo',
		'getrawmempool',
		'getmempoolentry',
		'getrawtransaction',
		'gettransaction',
		'importaddress',
		'listaccounts',
		'listlabels',
		'listunspent',
		'setlabel',
		'sendrawtransaction',
		'signrawtransaction',
		'signrawtransactionwithkey', # method new to Core v0.17.0
		'validateaddress',
		'walletpassphrase',
	)

class EthereumRPCConnection(RPCConnection):

	auth = False
	db_fs = '    host [{h}] port [{p}]\n'

	rpcmethods = (
		'eth_accounts',
		'eth_blockNumber',
		'eth_call',
		# Returns the EIP155 chain ID used for transaction signing at the current best block.
		# Null is returned if not available.
		'eth_chainId',
		'eth_gasPrice',
		'eth_getBalance',
		'eth_getBlockByHash',
		'eth_getBlockByNumber',
		'eth_getCode',
		'eth_getTransactionByHash',
		'eth_getTransactionReceipt',
		'eth_protocolVersion',
		'eth_sendRawTransaction',
		'eth_signTransaction',
		'eth_syncing',
		'net_listening',
		'net_peerCount',
		'net_version',
		'parity_chain',
		'parity_chainId', # superseded by eth_chainId
		'parity_chainStatus',
		'parity_composeTransaction',
		'parity_gasCeilTarget',
		'parity_gasFloorTarget',
		'parity_localTransactions',
		'parity_minGasPrice',
		'parity_mode',
		'parity_netPeers',
		'parity_nextNonce',
		'parity_nodeKind',
		'parity_nodeName',
		'parity_pendingTransactions',
		'parity_pendingTransactionsStats',
		'parity_versionInfo',
	)

class MoneroWalletRPCConnection(RPCConnection):
	rpcmethods = (
		'get_version',
		'get_height',    # sync height of the open wallet
		'get_balance',   # { "account_index":0,"address_indices":[0,1] }
		'create_wallet', # { "filename":"name","password":"passw0rd","language":"English" }
		'open_wallet',   # { "filename":"name","password":"passw0rd" }
		'close_wallet',
		'restore_deterministic_wallet', # name,password,seed (restore_height,language,seed_offset,autosave_current)
		'refresh',       # {"start_height":100000}
	)

	def request(self,cmd,*args,**kwargs):
		from subprocess import run,PIPE
		data = {
			'jsonrpc': '2.0',
			'id': '0',
			'method': cmd,
			'params': kwargs,
		}
		exec_cmd = [
			'curl', '--proxy', '', '--silent','--insecure', '--request', 'POST',
			'--digest', '--user', '{}:{}'.format(g.monero_wallet_rpc_user,g.monero_wallet_rpc_password),
			'--header', 'Content-Type: application/json',
			'--data', json.dumps(data),
			'https://{}:{}/json_rpc'.format(self.host,self.port) ]

		cp = run(exec_cmd,stdout=PIPE,check=True)

		res = json.loads(cp.stdout)
		if 'error' in res:
			raise RPCFailure(repr(res['error']))
		return(res['result'])

def rpc_error(ret):
	return type(ret) is tuple and ret and ret[0] == 'rpcfail'

def rpc_errmsg(ret):
	try:
		return ret[1][2]
	except:
		return repr(ret)

def init_daemon_parity():

	def resolve_token_arg(token_arg):
		from mmgen.obj import CoinAddr
		from mmgen.altcoins.eth.tw import EthereumTrackingWallet
		from mmgen.altcoins.eth.contract import Token

		tw = EthereumTrackingWallet(no_rpc=True)

		try:    addr = CoinAddr(token_arg,on_fail='raise')
		except: addr = tw.sym2addr(token_arg)

		if not addr:
			m = "'{}': unrecognized token symbol"
			raise UnrecognizedTokenSymbol(m.format(token_arg))

		sym = tw.addr2sym(addr) # throws exception on failure
		vmsg('ERC20 token resolved: {} ({})'.format(addr,sym))

		return addr,sym

	conn = EthereumRPCConnection(
				g.rpc_host or 'localhost',
				g.rpc_port or g.proto.rpc_port)

	conn.daemon_version = conn.parity_versionInfo()['version'] # fail immediately if daemon is geth
	conn.coin_amt_type = str
	g.chain = conn.parity_chain().replace(' ','_')

	conn.caps = ()
	try:
		conn.request('eth_chainId')
		conn.caps += ('eth_chainId',)
	except RPCFailure:
		pass

	if conn.request('parity_nodeKind')['capability'] == 'full':
		conn.caps += ('full_node',)

	if g.token:
		g.rpch = conn # set g.rpch so rpc_init() will return immediately
		(g.token,g.dcoin) = resolve_token_arg(g.token)

	return conn

def init_daemon_bitcoind():

	def check_chainfork_mismatch(conn):
		block0 = conn.getblockhash(0)
		latest = conn.getblockcount()
		try:
			assert block0 == g.proto.block0,'Incorrect Genesis block for {}'.format(g.proto.__name__)
			for fork in g.proto.forks:
				if fork[0] == None or latest < fork[0]: break
				assert conn.getblockhash(fork[0]) == fork[1], (
					'Bad block hash at fork block {}. Is this the {} chain?'.format(fork[0],fork[2].upper()))
		except Exception as e:
			die(2,"{}\n'{c}' requested, but this is not the {c} chain!".format(e.args[0],c=g.coin))

	def check_chaintype_mismatch():
		try:
			if g.regtest: assert g.chain == 'regtest','--regtest option selected, but chain is not regtest'
			if g.testnet: assert g.chain != 'mainnet','--testnet option selected, but chain is mainnet'
			if not g.testnet: assert g.chain == 'mainnet','mainnet selected, but chain is not mainnet'
		except Exception as e:
			die(1,'{}\nChain is {}!'.format(e.args[0],g.chain))

	cfg = get_daemon_cfg_options(('rpcuser','rpcpassword'))

	conn = RPCConnection(
				g.rpc_host or 'localhost',
				g.rpc_port or g.proto.rpc_port,
				g.rpc_user or cfg['rpcuser'], # MMGen's rpcuser,rpcpassword override coin daemon's
				g.rpc_password or cfg['rpcpassword'],
				auth_cookie=get_coin_daemon_auth_cookie())

	if g.bob or g.alice:
		from mmgen.regtest import MMGenRegtest
		MMGenRegtest(g.coin).switch_user(('alice','bob')[g.bob],quiet=True)
	conn.daemon_version = int(conn.getnetworkinfo()['version'])
	conn.coin_amt_type = (float,str)[conn.daemon_version>=120000]
	g.chain = conn.getblockchaininfo()['chain']
	if g.chain != 'regtest': g.chain += 'net'
	assert g.chain in g.chains
	check_chaintype_mismatch()

	if g.chain == 'mainnet': # skip this for testnet, as Genesis block may change
		check_chainfork_mismatch(conn)

	conn.caps = ('full_node',)
	for func,cap in (
		('setlabel','label_api'),
		('signrawtransactionwithkey','sign_with_key') ):
		if len(conn.request('help',func).split('\n')) > 3:
			conn.caps += (cap,)
	return conn

def init_daemon(name):
	return globals()['init_daemon_'+name]()

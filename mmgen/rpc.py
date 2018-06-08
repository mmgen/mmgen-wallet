#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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

import httplib,base64,json

from mmgen.common import *
from decimal import Decimal

def dmsg_rpc(s):
	if g.debug_rpc: msg(s)

class RPCFailure(Exception): pass

class CoinDaemonRPCConnection(object):

	auth = True
	db_fs = '    host [{h}] port [{p}] user [{u}] passwd [{pw}] auth_cookie [{c}]\n'

	def __init__(self,host=None,port=None,user=None,passwd=None,auth_cookie=None):

		dmsg_rpc('=== {}.__init__() debug ==='.format(type(self).__name__))
		dmsg_rpc(self.db_fs.format(h=host,p=port,u=user,pw=passwd,c=auth_cookie))

		import socket
		try:
			socket.create_connection((host,port),timeout=3).close()
		except:
			die(1,'Unable to connect to {}:{}'.format(host,port))

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

		self.host = host
		self.port = port

		for method in self.rpcmethods:
			exec '{c}.{m} = lambda self,*args,**kwargs: self.request("{m}",*args,**kwargs)'.format(
						c=type(self).__name__,m=method)

	# Normal mode: call with arg list unrolled, exactly as with cli
	# Batch mode:  call with list of arg lists as first argument
	# kwargs are for local use and are not passed to server

	# By default, dies with an error msg on all errors and exceptions
	# on_fail is one of 'die' (default), 'return', 'silent', 'raise'
	# With on_fail='return', returns 'rpcfail',(resp_object,(die_args))
	def request(self,cmd,*args,**kwargs):

		if os.getenv('MMGEN_RPC_FAIL_ON_COMMAND') == cmd:
			cmd = 'badcommand_' + cmd

		cf = { 'timeout':g.http_timeout, 'batch':False, 'on_fail':'die' }

		for k in cf:
			if k in kwargs and kwargs[k]: cf[k] = kwargs[k]

		hc = httplib.HTTPConnection(self.host, self.port, False, cf['timeout'])

		if cf['batch']:
			p = [{'method':cmd,'params':r,'id':n,'jsonrpc':'2.0'} for n,r in enumerate(args[0],1)]
		else:
			p = {'method':cmd,'params':args,'id':1,'jsonrpc':'2.0'}

		def do_fail(*args):
			if cf['on_fail'] in ('return','silent'):
				return 'rpcfail',args

			try:    s = u'{}'.format(args[2])
			except: s = repr(args[2])

			if cf['on_fail'] == 'raise':
				raise RPCFailure,s
			elif cf['on_fail'] == 'die':
				die(args[1],yellow(s))

		dmsg_rpc('=== request() debug ===')
		dmsg_rpc('    RPC POST data ==> {}\n'.format(p))

		class MyJSONEncoder(json.JSONEncoder):
			def default(self,obj):
				if isinstance(obj,g.proto.coin_amt):
					return g.proto.get_rpc_coin_amt_type()(obj)
				return json.JSONEncoder.default(self,obj)

		http_hdr = { 'Content-Type': 'application/json' }
		if self.auth:
			fs = '    RPC AUTHORIZATION data ==> raw: [{}]\n{:>31}enc: [Basic {}]\n'
			as_enc = base64.b64encode(self.auth_str)
			dmsg_rpc(fs.format(self.auth_str,'',as_enc))
			http_hdr.update({ 'Host':self.host, 'Authorization':'Basic {}'.format(as_enc) })

		try:
			hc.request('POST','/',json.dumps(p,cls=MyJSONEncoder),http_hdr)
		except Exception as e:
			m = '{}\nUnable to connect to {} at {}:{}'
			return do_fail(None,2,m.format(e,g.proto.daemon_name,self.host,self.port))

		try:
			r = hc.getresponse() # returns HTTPResponse instance
		except Exception:
			m = 'Unable to connect to {} at {}:{} (but port is bound?)'
			return do_fail(None,2,m.format(g.proto.daemon_name,self.host,self.port))

		dmsg_rpc('    RPC GETRESPONSE data ==> {}\n'.format(r.__dict__))

		if r.status != 200:
			if cf['on_fail'] not in ('silent','raise'):
				msg_r(yellow('{} RPC Error: '.format(g.proto.daemon_name.capitalize())))
				msg(red('{} {}'.format(r.status,r.reason)))
			e1 = r.read()
			try:
				e3 = json.loads(e1)['error']
				e2 = '{} (code {})'.format(e3['message'],e3['code'])
			except:
				e2 = str(e1)
			return do_fail(r,1,e2)

		r2 = r.read().decode('utf8')

		dmsg_rpc(u'    RPC REPLY data ==> {}\n'.format(r2))

		if not r2:
			return do_fail(r,2,'Error: empty reply')

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
		'getbalance',
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
		'listunspent',
		'sendrawtransaction',
		'signrawtransaction',
		'validateaddress',
		'walletpassphrase',
	)

class EthereumRPCConnection(CoinDaemonRPCConnection):

	auth = False
	db_fs = '    host [{h}] port [{p}]\n'

	rpcmethods = (
		'eth_accounts',
		'eth_blockNumber',
		'eth_call',
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
		# Returns the EIP155 chain ID used for transaction signing at the current best block.
		# Null is returned if not available.
		'parity_chainId',
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

def rpc_error(ret):
	return type(ret) is tuple and ret and ret[0] == 'rpcfail'

def rpc_errmsg(ret): return ret[1][2]

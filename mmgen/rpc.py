#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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
rpc.py:  Bitcoin RPC library for the MMGen suite
"""

import httplib,base64,json

from mmgen.common import *
from decimal import Decimal
from mmgen.obj import BTCAmt

class BitcoinRPCConnection(object):

	client_version = 0

	def __init__(
				self,
				host='localhost',port=(8332,18332)[g.testnet],
				user=None,passwd=None,auth_cookie=None,
			):

		if auth_cookie:
			self.auth_str = auth_cookie
		elif user and passwd:
			self.auth_str = '{}:{}'.format(user,passwd)
		else:
			msg('Error: no Bitcoin RPC authentication method found')
			if passwd: die(1,"'rpcuser' entry missing in bitcoin.conf")
			elif user: die(1,"'rpcpassword' entry missing in bitcoin.conf")
			else:
				m1 = 'Either provide rpcuser/rpcpassword in bitcoin.conf'
				m2 = '(or, alternatively, copy the authentication cookie to Bitcoin data dir'
				m3 = 'if {} and Bitcoin are running as different users)'.format(g.proj_name)
				die(1,'\n'.join((m1,m2,m3)))

		self.host = host
		self.port = port

	# Normal mode: call with arg list unrolled, exactly as with 'bitcoin-cli'
	# Batch mode:  call with list of arg lists as first argument
	# kwargs are for local use and are not passed to server

	# By default, dies with an error msg on all errors and exceptions
	# With on_fail='return', returns 'rpcfail',(resp_object,(die_args))
	def request(self,cmd,*args,**kwargs):

		cf = { 'timeout':g.http_timeout, 'batch':False, 'on_fail':'die' }

		for k in cf:
			if k in kwargs and kwargs[k]: cf[k] = kwargs[k]

		hc = httplib.HTTPConnection(self.host, self.port, False, cf['timeout'])

		if cf['batch']:
			p = [{'method':cmd,'params':r,'id':n} for n,r in enumerate(args[0],1)]
		else:
			p = {'method':cmd,'params':args,'id':1}

		def die_maybe(*args):
			if cf['on_fail'] == 'return':
				return 'rpcfail',args
			else:
				die(*args[1:])

		dmsg('=== rpc.py debug ===')
		dmsg('    RPC POST data ==> %s\n' % p)

		caller = self
		class MyJSONEncoder(json.JSONEncoder):
			def default(self, obj):
				if isinstance(obj, BTCAmt):
					return (float,str)[caller.client_version>=120000](obj)
				return json.JSONEncoder.default(self, obj)

# Can't do UTF-8 labels yet: httplib only ascii?
# 		if type(p) != list and p['method'] == 'importaddress':
# 			dump = json.dumps(p,cls=MyJSONEncoder,ensure_ascii=False)
# 			print(dump)

		try:
			hc.request('POST', '/', json.dumps(p,cls=MyJSONEncoder), {
				'Host': self.host,
				'Authorization': 'Basic ' + base64.b64encode(self.auth_str)
			})
		except Exception as e:
			return die_maybe(None,2,'%s\nUnable to connect to bitcoind' % e)

		r = hc.getresponse() # returns HTTPResponse instance

		if r.status != 200:
			msgred('RPC Error: {} {}'.format(r.status,r.reason))
			e1 = r.read()
			try:
				e2 = json.loads(e1)['error']['message']
			except:
				e2 = str(e1)
			return die_maybe(r,1,e2)

		r2 = r.read()

		dmsg('    RPC REPLY data ==> %s\n' % r2)

		if not r2:
			return die_maybe(r,2,'Error: empty reply')

#		from decimal import Decimal
		r3 = json.loads(r2.decode('utf8'), parse_float=Decimal)
		ret = []

		for resp in r3 if cf['batch'] else [r3]:
			if 'error' in resp and resp['error'] != None:
				return die_maybe(r,1,'Bitcoind returned an error: %s' % resp['error'])
			elif 'result' not in resp:
				return die_maybe(r,1, 'Missing JSON-RPC result\n' + repr(resps))
			else:
				ret.append(resp['result'])

		return ret if cf['batch'] else ret[0]


	rpcmethods = (
		'createrawtransaction',
		'backupwallet',
		'decoderawtransaction',
		'estimatefee',
		'getaddressesbyaccount',
		'getbalance',
		'getblock',
		'getblockcount',
		'getblockhash',
		'getinfo',
		'importaddress',
		'listaccounts',
		'listunspent',
		'sendrawtransaction',
		'signrawtransaction',
		'getrawmempool',
	)

	for name in rpcmethods:
		exec "def {n}(self,*a,**k):return self.request('{n}',*a,**k)\n".format(n=name)

def rpc_error(ret):
	return type(ret) is tuple and ret and ret[0] == 'rpcfail'

def rpc_errmsg(ret): return ret[1][2]

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

import httplib,base64,json,decimal

from mmgen.common import *

class BitcoinRPCConnection(object):

	def __init__(
				self,
				host='localhost',port=8332,
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
	def request(self,cmd,*args,**kwargs):

		cf = { 'timeout': g.http_timeout, 'batch': False }

		for k in cf:
			if k in kwargs and kwargs[k]: cf[k] = kwargs[k]

		c = httplib.HTTPConnection(self.host, self.port, False, cf['timeout'])

		if cf['batch']:
			p = [{'method':cmd,'params':r,'id':n} for n,r in enumerate(args[0],1)]
		else:
			p = {'method':cmd,'params':args,'id':1}

		dmsg('=== rpc.py debug ===')
		dmsg('    RPC POST data ==> %s\n' % p)

		try:
			c.request('POST', '/', json.dumps(p), {
				'Host': self.host,
				'Authorization': 'Basic ' + base64.b64encode(self.auth_str)
			})
		except Exception as e:
			die(2,'%s\nUnable to connect to bitcoind' % e)

		r = c.getresponse() # returns HTTPResponse instance

		if r.status == 401:
			m1 = 'RPC authentication error'
			m2 = 'Check that rpcuser/rpcpassword in Bitcoin config file are correct'
			m3 = '(or, alternatively, copy the authentication cookie to Bitcoin data dir'
			m4 = 'if {} and Bitcoin are running as different users)'.format(g.proj_name)
			die(1,'\n'.join((m1,m2,m3,m4)))
		elif r.status != 200:
			die(1,'RPC error: %s %s\n%s' % (r.status, r.reason, r.read()))

		r2 = r.read()

		dmsg('    RPC REPLY data ==> %s\n' % r2)

		if not r2:
			die(2,'Error: empty reply')

		r3 = json.loads(r2.decode('utf8'), parse_float=decimal.Decimal)
		ret = []

		for resp in r3 if cf['batch'] else [r3]:
			if 'error' in resp and resp['error'] != None:
				die(1,'Bitcoind returned an error: %s' % resp['error'])
			elif 'result' not in resp:
				die(1, 'Missing JSON-RPC result\n' + repr(resps))
			else:
				ret.append(resp['result'])

		return ret if cf['batch'] else ret[0]


	rpcmethods = (
		'estimatefee',
		'getinfo',
		'getbalance',
		'getaddressesbyaccount',
		'listunspent',
		'listaccounts',
		'importaddress',
		'decoderawtransaction',
		'createrawtransaction',
		'signrawtransaction',
		'sendrawtransaction',
		'walletpassphrase',
		'walletlock',
	)

	for name in rpcmethods:
		exec "def {n}(self,*a,**k):return self.request('{n}',*a,**k)\n".format(n=name)

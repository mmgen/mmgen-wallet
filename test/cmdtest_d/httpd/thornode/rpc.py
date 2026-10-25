# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_d.httpd.thornode.rpc: Thornode RPC HTTP server
"""

import re, json
from wsgiref.util import request_uri

from mmgen.cfg import Config

from . import ThornodeServer, make_inbound_addr

def get_inbounds_info():
	with open('test/ref/thorchain/inbound.json') as fh:
		data = json.loads(fh.read())
	for d in data:
		d['address'] = make_inbound_addr(d['chain'])
	return data

class ThornodeRPCServer(ThornodeServer):
	port = 18800
	name = 'thornode RPC server'

	ping_info = {'ping': 'pong'}

	mimir_info = {
		'ASGARDSIZE': 20,
		'CHURNINTERVAL': 43200,
		'HALTBTCCHAIN': 0,
		'HALTMEMOLESS': 0,
		'MEMOLESSTXNCOST': 200000}

	lastblock_info = [{
			'chain': 'BTC',
			'last_observed_in': 969302,
			'last_signed_out': 28043381,
			'thorchain': 28043387
		}, {
			'chain': 'ETH',
			'last_observed_in': 26090346,
			'last_signed_out': 28043381,
			'thorchain': 28043387}]

	memo_info = {
		'0c7454c0': { # 0c7454c06d3fc0e520d34283e6f491ce7afe5abb3f569bbdfea1732e04b716ec
			'reference': '13579',
			'asset': 'LTC.LTC',
			'memo': '=:c:qq6myf0qd6q5tln96ntl37hq0u7940w2xvs9jsuqv0:7967e4/3/0',
			'height': '12345678'},
		'fbbbd382': { # fbbbd382edd2d5478e0316b6c31ef6a0bbad57bcebc9d8b30cc52e5dbf107622
			'reference': '78787',
			'asset': 'XMR.XMR',
			'memo': '=:l:rltc1q6rs4znw8kajd6n6yn2snlfra3pluz3x5paj6x3:0/3/0',
			'height': '12349876'},
		'ae04ecd8': { # ae04ecd8ff1f0c13861bd2d6123ce33ea03a731ccd142f5ca2f2450a54f215ba
			'reference': '98765',
			'asset': 'LTC.LTC',
			'memo': '=:XMR.XMR:88u4waXXrPUD9EkCGMcFifKJakDZ6vx6zNpePuS238SLP7ziiMuqeP31c8ftJEDSymcSK88FFzKvQfoohF4LSyFu5E3yWTH:0/3/0',
			'height': '12346789'}}

	refreq_txid_xmr = 'fbbbd382edd2d5478e0316b6c31ef6a0bbad57bcebc9d8b30cc52e5dbf107622'

	inbounds_info = get_inbounds_info()

	var_actions = {
		'halt_memoless':   ('mimir_info', 'HALTMEMOLESS'),
		'memoless_tx_fee': ('mimir_info', 'MEMOLESSTXNCOST')}

	chain_var_actions = {
		'ltc_global_paused': ('inbounds_info', 'LTC', 'global_trading_paused'),
		'ltc_paused':        ('inbounds_info', 'LTC', 'chain_trading_paused'),
		'ltc_halted':        ('inbounds_info', 'LTC', 'halted'),
		'bch_halted':        ('inbounds_info', 'BCH', 'halted')}

	def make_response_body(self, method, environ):

		class responses:

			# pylint: disable=unsubscriptable-object

			def balance(m, length):
				return [
					{'denom': 'foocoin', 'amount': 321321321321},
					{'denom': 'rune',    'amount': 987654321321},
					{'denom': 'barcoin', 'amount': 123123123123}]

			def acct_info(m, length):
				return {
					'value': {
						'address': m[1],
						'pub_key': 'PubKeySecp256k1{0000}',
						'account_number': '1234',
						'sequence': '333444'}}

			def tx_info(m, length):
				txid = environ['wsgi.input'].read(length).decode().removeprefix('hash=0x').upper()
				return {
					'hash': txid,
					'height': '21298600',
					'index': 2,
					'tx_result': {
						'gas_used': '173222',
						'events': [],
						'codespace': ''
					},
					'tx': 'MHgwMGZvb2Jhcg=='}

			def check_tx(m, length):
				return {
					'code': 0,
					'data': '',
					'log': '',
					'info': '',
					'gas_wanted': '-1',
					'gas_used': '53774',
					'events': [],
					'codespace': ''}

			def broadcast_tx_sync(m, length):
				from mmgen.proto.rune.tx.protobuf import RuneTx
				txhex = environ['wsgi.input'].read(length).decode().removeprefix('tx=0x').upper()
				tx = RuneTx.loads(bytes.fromhex(txhex))
				return {'code': 0, 'codespace': '', 'data': '', 'log': '', 'hash': tx.txid}

			def ping(m, length):
				return self.ping_info

			def mimir(m, length):
				return self.mimir_info

			def lastblock(m, length):
				return self.lastblock_info

			def get_refnum(m, length):
				return self.memo_info[m[1].lower()[:8]]

			def validate_refnum(m, length):
				for v in self.memo_info.values():
					if v['asset'] == m[1] and v['reference'] == m[2]:
						return v

			def validate_amt(m, length):
				from mmgen.swap.util import get_swap_asset, init_swap_proto # pylint: disable=all
				from mmgen.swap.proto.thorchain.memoless import THORChainMemolessAmount # pylint: disable=all

				cfg = Config()
				swap_asset = get_swap_asset(cfg, m[1], sanitize_input=True)
				amt = init_swap_proto(cfg, swap_asset).coin_amt(int(m[2]), from_unit='atomic')
				ma = THORChainMemolessAmount(amt)

				for v in self.memo_info.values():
					if v['asset'] == m[1] and int(v['reference']) == ma.refnum:
						mi = v
						break
				else:
					raise ValueError(f'No reference matching asset {m[1]} and refnum {ma.refnum}')

				return {
					'reference': ma.refnum,
					'available': True,
					'can_register': True,
					'expires_at': 9999999999,
					'memo': mi['memo'],
					'usage_count': 0,
					'max_use': 1} # 0 = unlimited

			def inbound_addrs(m, length):
				return self.inbounds_info

		pat_info = ( # these are matched in order, so more specific patterns must go first
			('ping',              'GET',  r'/thorchain/ping'),
			('mimir',             'GET',  r'/thorchain/mimir'),
			('lastblock',         'GET',  r'/thorchain/lastblock(.*)'),
			('inbound_addrs',     'GET',  r'/thorchain/inbound_addresses'),
			('validate_amt',      'GET',  r'/thorchain/memo/check/(\S+)/(\S+)'),
			('validate_refnum',   'GET',  r'/thorchain/memo/(\S+)/(\S+)'),
			('get_refnum',        'GET',  r'/thorchain/memo/(\S+)'),
			('balance',           'GET',  r'/bank/balances/(\S+)'),
			('acct_info',         'GET',  r'/auth/accounts/(\S+)'),
			('tx_info',           'POST', r'/tx$'),
			('check_tx',          'POST', r'/check_tx$'),
			('broadcast_tx_sync', 'POST', r'/broadcast_tx_sync$'))

		req_str = request_uri(environ)

		for name, method_chk, pat in pat_info:
			if m := re.search(pat, req_str):
				assert method == method_chk
				length = int(environ.get('CONTENT_LENGTH', '0')) if method == 'POST' else None
				res = getattr(responses, name)(m, length)
				return json.dumps({'result': res}).encode()

		raise ValueError(f'‘{req_str}’: malformed query path')

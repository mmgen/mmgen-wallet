#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.tx_proxy: tx proxy classes
"""

from ..color import green, pink, orange
from ..util import msg, msg_r, die
from ..http import HTTPClient

class TxProxyClient(HTTPClient):

	def get_form(self, timeout=None):
		return self.get(path=self.form_path, timeout=timeout)

	def post_form(self, *, data, timeout=None):
		return self.post(path=self.form_path, data=data, timeout=timeout)

	def get_form_element(self, text):
		from lxml import html
		root = html.document_fromstring(text)
		res = [e for e in root.forms if e.attrib.get('action', '').endswith(self.form_path)]
		assert res, 'no matching forms!'
		assert len(res) == 1, 'more than one matching form!'
		return res[0]

	def cache_fn(self, desc, *, extra_desc=None):
		return '{}-{}{}.html'.format(self.name, desc, f'-{extra_desc}' if extra_desc else '')

	def save_response(self, data, desc, *, extra_desc=None):
		from ..fileutil import write_data_to_file
		write_data_to_file(
			self.cfg,
			self.cache_fn(desc, extra_desc=extra_desc),
			data,
			desc = f'{desc} page from {orange(self.host)}')

class BlockchairTxProxyClient(TxProxyClient):

	name = 'blockchair'
	host = 'blockchair.com'
	form_path = '/broadcast'
	assets = {
		'avax': 'avalanche',
		'btc':  'bitcoin',
		'bch':  'bitcoin-cash',
		'bnb':  'bnb',
		'dash': 'dash',
		'doge': 'dogecoin',
		'eth':  'ethereum',
		'etc':  'ethereum-classic',
		'ltc':  'litecoin',
		'zec':  'zcash'}
	active_assets = () # tried with ETH, doesn’t work

	def create_post_data(self, *, form_text, coin, tx_hex):

		coin = coin.lower()
		assert coin in self.assets, f'coin {coin} not supported by {self.name}'
		asset = self.assets[coin]

		form = self.get_form_element(form_text)
		data = {}

		e = form.find('.//input')
		assert e.attrib['name'] == '_token', 'input name incorrect!'
		data['_token'] = e.attrib['value']

		e = form.find('.//textarea')
		assert e.attrib['name'] == 'data', 'textarea name incorrect!'
		data['data'] = '0x' + tx_hex

		e = form.find('.//button')
		assert e is not None, 'missing button!'

		e = form.find('.//select')
		assert e.attrib['name'] == 'blockchain', 'select element name incorrect!'

		assets = [f.get('value') for f in e.iter() if f.get('value')]
		assert asset in assets, f'coin {coin} ({asset}) not currently supported by {self.name}'

		data['blockchain'] = asset

		return data

	def get_txid(self, *, result_text):
		msg(f'Response parsing TBD.  Check the cached response at {self.cache_fn("result")}')

class EtherscanTxProxyClient(TxProxyClient):
	name = 'etherscan'
	host = 'etherscan.io'
	form_path = '/pushTx'
	assets = {'eth': 'ethereum'}
	active_assets = ('eth',)

	def create_post_data(self, *, form_text, coin, tx_hex):

		form = self.get_form_element(form_text)
		data = {}

		for e in form.findall('.//input'):
			data[e.attrib['name']] = e.attrib['value']

		if len(data) != 4:
			msg('')
			self.save_response(form_text, 'form')
			die(3, f'{len(data)}: unexpected number of keys in data (expected 4)')

		e = form.find('.//textarea')
		data[e.attrib['name']] = '0x' + tx_hex

		return data

	def get_txid(self, *, result_text):
		import json
		from ..obj import CoinTxID, is_coin_txid
		form = self.get_form_element(result_text)
		json_text = form.find('div/div/div')[1].tail
		txid = None
		try:
			txid = json.loads(json_text)['result'].removeprefix('0x')
		except json.JSONDecodeError:
			msg(json_text)
		except Exception as e:
			msg(f'{type(e).__name__}: {e}')
		return CoinTxID(txid) if is_coin_txid(txid) else False

def send_tx(cfg, txhex):

	c = get_client(cfg)
	msg(f'Using {pink(cfg.tx_proxy.upper())} tx proxy')

	msg_r(f'Retrieving form from {orange(c.host)}...')
	form_text = c.get_form(timeout=180)
	msg('done')

	msg_r('Parsing form...')
	post_data = c.create_post_data(
		form_text = form_text,
		coin      = cfg.coin,
		tx_hex    = txhex)
	msg('done')

	if cfg.test:
		msg(f'Form retrieved from {orange(c.host)} and parsed')
		msg(green('Transaction can be sent'))
		return False

	msg_r('Sending data...')
	result_text = c.post_form(data=post_data, timeout=180)
	msg('done')

	msg_r('Parsing response...')
	txid = c.get_txid(result_text=result_text)
	msg('done')

	msg('Transaction ' + (f'sent: {txid.hl()}' if txid else 'send failed'))
	c.save_response(result_text, 'result', extra_desc=txid)

	return txid

tx_proxies = {
	'blockchair': BlockchairTxProxyClient,
	'etherscan':  EtherscanTxProxyClient
}

def get_client(cfg, *, check_only=False):
	proxy = tx_proxies[cfg.tx_proxy]
	if cfg.coin.lower() in proxy.active_assets:
		return True if check_only else proxy(cfg)
	else:
		die(1, f'Coin {cfg.coin} not supported by TX proxy {pink(proxy.name.upper())}')

def check_client(cfg):
	return get_client(cfg, check_only=True)

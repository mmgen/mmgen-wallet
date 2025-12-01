#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
tx.file: Transaction file operations for the MMGen suite
"""

import os, json

from ..util import ymsg, make_chksum_6, die
from ..obj import MMGenObject, HexStr, MMGenTxID, CoinTxID, MMGenTxComment

def get_monero_proto(tx, data):
	from ..protocol import init_proto
	return init_proto(tx.cfg, 'XMR', network=data['MoneroMMGenTX']['data']['network'])

class txdata_json_encoder(json.JSONEncoder):
	def default(self, o):
		if type(o).__name__.endswith('Amt'):
			return str(o)
		elif type(o).__name__ == 'OpReturnData':
			return repr(o)
		else:
			return json.JSONEncoder.default(self, o)

def json_dumps(data):
	return json.dumps(data, separators = (',', ':'), cls=txdata_json_encoder)

def get_proto_from_coin_id(tx, coin_id, chain):
	coin, tokensym = coin_id.split(':') if ':' in coin_id else (coin_id, None)

	from ..protocol import CoinProtocol, init_proto
	network = CoinProtocol.Base.chain_name_to_network(tx.cfg, coin, chain)

	return init_proto(tx.cfg, coin, network=network, need_amt=True, tokensym=tokensym)

def eval_io_data(tx, data, *, desc):
	if not (desc == 'outputs' and tx.proto.base_coin == 'ETH'): # ETH txs can have no outputs
		assert len(data), f'no {desc}!'
	for d in data:
		d['amt'] = tx.proto.coin_amt(d['amt'])
	io, io_list = {
		'inputs':  (tx.Input, tx.InputList),
		'outputs': (tx.Output, tx.OutputList),
	}[desc]
	return io_list(parent=tx, data=[io(tx.proto, **d) for d in data])

class MMGenTxFile(MMGenObject):
	data_label = 'MMGenTransaction'
	attrs = {
		'chain': None,
		'txid': MMGenTxID,
		'send_amt': 'skip',
		'timestamp': None,
		'blockcount': None,
		'serialized': None}
	extra_attrs = {
		'locktime': None,
		'comment': MMGenTxComment,
		'coin_txid': CoinTxID,
		'sent_timestamp': None,
		'is_swap': None}

	def __init__(self, tx):
		self.tx       = tx
		self.fmt_data = None
		self.filename = None

	def parse(self, infile, *, metadata_only=False, quiet_open=False):
		tx = self.tx
		from ..fileutil import get_data_from_file
		data = get_data_from_file(tx.cfg, infile, desc=f'{tx.desc} data', quiet=quiet_open)
		if len(data) > tx.cfg.max_tx_file_size:
			die('MaxFileSizeExceeded',
				f'Transaction file size exceeds limit ({tx.cfg.max_tx_file_size} bytes)')
		return (self.parse_data_json if data[0] == '{' else self.parse_data_legacy)(data, metadata_only)

	def parse_data_json(self, data, metadata_only):
		tx = self.tx
		tx.file_format = 'json'
		outer_data = json.loads(data)
		if 'MoneroMMGenTX' in outer_data:
			tx.proto = get_monero_proto(tx, outer_data)
			return None
		data = outer_data[self.data_label]
		if outer_data['chksum'] != make_chksum_6(json_dumps(data)):
			chk = make_chksum_6(json_dumps(data))
			die(3, f'{self.data_label}: invalid checksum for TxID {data["txid"]} ({chk} != {outer_data["chksum"]})')

		tx.proto = get_proto_from_coin_id(tx, data['coin_id'], data['chain'])

		for k, v in self.attrs.items():
			if v != 'skip':
				setattr(tx, k, v(data[k]) if v else data[k])

		if metadata_only:
			return

		for k, v in self.extra_attrs.items():
			if k in data:
				setattr(tx, k, v(data[k]) if v else data[k])

		if tx.is_swap:
			for k, v in tx.swap_attrs.items():
				if k in data:
					setattr(tx, k, v(data[k]) if v else data[k])

		for k in ('inputs', 'outputs'):
			setattr(tx, k, eval_io_data(tx, data[k], desc=k))

		tx.check_txfile_hex_data()

		tx.parse_txfile_serialized_data() # Ethereum RLP or JSON data

		assert tx.proto.coin_amt(data['send_amt']) == tx.send_amt, f'{data["send_amt"]} != {tx.send_amt}'

	def parse_data_legacy(self, data, metadata_only):
		tx = self.tx
		tx.file_format = 'legacy'

		def deserialize(raw_data, *, desc):
			from ast import literal_eval
			try:
				return literal_eval(raw_data)
			except:
				if desc == 'inputs':
					ymsg('Warning: transaction data appears to be in old format')
				import re
				return literal_eval(re.sub(r"[A-Za-z]+?\(('.+?')\)", r'\1', raw_data))

		desc = 'data'
		try:
			tx_data = data.splitlines()
			assert len(tx_data) >= 5, 'number of lines less than 5'
			assert len(tx_data[0]) == 6, 'invalid length of first line'
			assert HexStr(tx_data.pop(0)) == make_chksum_6(' '.join(tx_data)), 'file data does not match checksum'

			if len(tx_data) == 7:
				desc = 'sent timestamp'
				(_, tx.sent_timestamp) = tx_data.pop(-1).split()
				assert _ == 'Sent', 'invalid sent timestamp line'

			if len(tx_data) == 6:
				assert len(tx_data[-1]) == 64, 'invalid coin TxID length'
				desc = 'coin TxID'
				tx.coin_txid = CoinTxID(tx_data.pop(-1))

			if len(tx_data) == 5:
				# rough check: allow for 4-byte utf8 characters + base58 (4 * 11 / 8 = 6 (rounded up))
				assert len(tx_data[-1]) < MMGenTxComment.max_len*6, 'invalid comment length'
				c = tx_data.pop(-1)
				if c != '-':
					desc = 'encoded comment (not base58)'
					from ..baseconv import baseconv
					comment = baseconv('b58').tobytes(c).decode()
					assert comment is not False, 'invalid comment'
					desc = 'comment'
					tx.comment = MMGenTxComment(comment)

			desc = 'number of lines' # four required lines
			io_data = {}
			(metadata, tx.serialized, io_data['inputs'], io_data['outputs']) = tx_data
			assert len(metadata) < 100, 'invalid metadata length' # rough check
			metadata = metadata.split()

			if metadata[-1].startswith('LT='):
				desc = 'locktime'
				tx.locktime = int(metadata.pop()[3:])

			desc = 'coin token in metadata'
			coin_id = metadata.pop(0) if len(metadata) == 6 else 'BTC'

			desc = 'chain token in metadata'
			tx.chain = metadata.pop(0).lower() if len(metadata) == 5 else 'mainnet'

			desc = 'coin_id or chain'
			tx.proto = get_proto_from_coin_id(tx, coin_id, tx.chain)

			desc = 'metadata (4 items)'
			(txid, send_amt, tx.timestamp, blockcount) = metadata

			desc = 'TxID in metadata'
			tx.txid = MMGenTxID(txid)
			desc = 'block count in metadata'
			tx.blockcount = int(blockcount)

			if metadata_only:
				return

			desc = 'transaction file hex data'
			tx.check_txfile_hex_data()
			desc = 'Ethereum RLP or JSON data'
			tx.parse_txfile_serialized_data()
			for k in ('inputs', 'outputs'):
				desc = f'{k} data'
				res = deserialize(io_data[k], desc=k)
				for d in res:
					if 'label' in d:
						d['comment'] = d['label']
						del d['label']
				setattr(tx, k, eval_io_data(tx, res, desc=k))
			desc = 'send amount in metadata'
			assert tx.proto.coin_amt(send_amt) == tx.send_amt, f'{send_amt} != {tx.send_amt}'
		except Exception as e:
			die(2, f'Invalid {desc} in transaction file: {e!s}')

	def make_filename(self):
		tx = self.tx
		def gen_filename():
			yield tx.txid
			if tx.coin != 'BTC':
				yield '-' + tx.dcoin
			yield f'[{tx.send_amt!s}'
			if tx.is_replaceable():
				yield ',{}'.format(tx.fee_abs2rel(tx.fee, to_unit=tx.fn_fee_unit))
			if tx.get_serialized_locktime():
				yield f',tl={tx.get_serialized_locktime()}'
			yield ']'
			if tx.proto.testnet:
				yield '.' + tx.proto.network
			yield '.' + tx.ext
		return ''.join(gen_filename())

	def format(self):
		tx = self.tx
		coin_id = tx.coin + ('' if tx.coin == tx.dcoin else ':'+tx.dcoin)

		def format_data_legacy():

			def amt_to_str(d):
				return {k: (str(d[k]) if k == 'amt' else d[k]) for k in d}

			lines = [
				'{}{} {} {} {} {}{}'.format(
					(f'{coin_id} ' if coin_id and tx.coin != 'BTC' else ''),
					tx.chain.upper(),
					tx.txid,
					tx.send_amt,
					tx.timestamp,
					tx.blockcount,
					(f' LT={tx.locktime}' if tx.locktime else ''),
				),
				tx.serialized,
				ascii([amt_to_str(e._asdict()) for e in tx.inputs]),
				ascii([amt_to_str(e._asdict()) for e in tx.outputs])
			]

			if tx.comment:
				from ..baseconv import baseconv
				lines.append(baseconv('b58').frombytes(tx.comment.encode(), tostr=True))

			if tx.coin_txid:
				if not tx.comment:
					lines.append('-') # keep old tx files backwards compatible
				lines.append(tx.coin_txid)

			if tx.sent_timestamp:
				lines.append(f'Sent {tx.sent_timestamp}')

			return '\n'.join([make_chksum_6(' '.join(lines))] + lines) + '\n'

		def format_data_json():
			data = json_dumps({
					'coin_id': coin_id
				} | {
					k: getattr(tx, k) for k in self.attrs
				} | {
					'inputs':  [e._asdict() for e in tx.inputs],
					'outputs': [{k: v for k,v in e._asdict().items()
						if not (type(v) is bool and v is False)} for e in tx.outputs]
				} | {
					k: getattr(tx, k) for k in self.extra_attrs if getattr(tx, k)
				} | ({
					k: getattr(tx, k) for k in tx.swap_attrs if getattr(tx, k, None)
				} if tx.is_swap else {}))
			return '{{"{}":{},"chksum":"{}"}}'.format(self.data_label, data, make_chksum_6(data))

		fmt_data = {'json': format_data_json, 'legacy': format_data_legacy}[tx.file_format]()

		if len(fmt_data) > tx.cfg.max_tx_file_size:
			die('MaxFileSizeExceeded', f'Transaction file size exceeds limit ({tx.cfg.max_tx_file_size} bytes)')

		return fmt_data

	def write(self, *,
		add_desc              = '',
		outdir                = None,
		ask_write             = True,
		ask_write_default_yes = False,
		ask_tty               = True,
		ask_overwrite         = True):

		if ask_write is False:
			ask_write_default_yes = True

		if not self.filename:
			self.filename = self.make_filename()

		if not self.fmt_data:
			self.fmt_data = self.format()

		from ..fileutil import write_data_to_file
		write_data_to_file(
			cfg                   = self.tx.cfg,
			outfile               = os.path.join((outdir or ''), self.filename),
			data                  = self.fmt_data,
			desc                  = self.tx.desc + add_desc,
			ask_overwrite         = ask_overwrite,
			ask_write             = ask_write,
			ask_tty               = ask_tty,
			ask_write_default_yes = ask_write_default_yes,
			ignore_opt_outdir     = outdir)

	@classmethod
	def get_proto(cls, cfg, filename, *, quiet_open=False):
		from . import BaseTX
		tmp_tx = BaseTX(cfg=cfg)
		cls(tmp_tx).parse(filename, metadata_only=True, quiet_open=quiet_open)
		return tmp_tx.proto

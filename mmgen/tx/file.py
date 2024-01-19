#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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

from ..util import ymsg,make_chksum_6,die
from ..obj import MMGenObject,HexStr,MMGenTxID,CoinTxID,MMGenTxComment

class MMGenTxFile(MMGenObject):

	def __init__(self,tx):
		self.tx       = tx
		self.chksum   = None
		self.fmt_data = None
		self.filename = None

	def parse(self,infile,metadata_only=False,quiet_open=False):
		tx = self.tx

		def eval_io_data(raw_data,desc):
			from ast import literal_eval
			try:
				d = literal_eval(raw_data)
			except:
				if desc == 'inputs' and not quiet_open:
					ymsg('Warning: transaction data appears to be in old format')
				import re
				d = literal_eval(re.sub(r"[A-Za-z]+?\(('.+?')\)",r'\1',raw_data))
			assert isinstance(d,list), f'{desc} data not a list!'
			if not (desc == 'outputs' and tx.proto.base_coin == 'ETH'): # ETH txs can have no outputs
				assert len(d), f'no {desc}!'
			for e in d:
				e['amt'] = tx.proto.coin_amt(e['amt'])
				if 'label' in e:
					e['comment'] = e['label']
					del e['label']
			io,io_list = {
				'inputs':  ( tx.Input, tx.InputList ),
				'outputs': ( tx.Output, tx.OutputList ),
			}[desc]
			return io_list( parent=tx, data=[io(tx.proto,**e) for e in d] )

		from ..fileutil import get_data_from_file
		tx_data = get_data_from_file( tx.cfg, infile, tx.desc+' data', quiet=quiet_open )

		desc = 'data'
		try:
			if len(tx_data) > tx.cfg.max_tx_file_size:
				die('MaxFileSizeExceeded',
					f'Transaction file size exceeds limit ({tx.cfg.max_tx_file_size} bytes)')
			tx_data = tx_data.splitlines()
			assert len(tx_data) >= 5,'number of lines less than 5'
			assert len(tx_data[0]) == 6,'invalid length of first line'
			self.chksum = HexStr(tx_data.pop(0))
			assert self.chksum == make_chksum_6(' '.join(tx_data)),'file data does not match checksum'

			if len(tx_data) == 6:
				assert len(tx_data[-1]) == 64,'invalid coin TxID length'
				desc = 'coin TxID'
				tx.coin_txid = CoinTxID(tx_data.pop(-1))

			if len(tx_data) == 5:
				# rough check: allow for 4-byte utf8 characters + base58 (4 * 11 / 8 = 6 (rounded up))
				assert len(tx_data[-1]) < MMGenTxComment.max_len*6,'invalid comment length'
				c = tx_data.pop(-1)
				if c != '-':
					desc = 'encoded comment (not base58)'
					from ..baseconv import baseconv
					comment = baseconv('b58').tobytes(c).decode()
					assert comment is not False,'invalid comment'
					desc = 'comment'
					tx.comment = MMGenTxComment(comment)

			desc = 'number of lines' # four required lines
			( metadata, tx.serialized, inputs_data, outputs_data ) = tx_data
			assert len(metadata) < 100,'invalid metadata length' # rough check
			metadata = metadata.split()

			if metadata[-1].startswith('LT='):
				desc = 'locktime'
				tx.locktime = int(metadata.pop()[3:])

			desc = 'coin token in metadata'
			coin = metadata.pop(0) if len(metadata) == 6 else 'BTC'
			coin,tokensym = coin.split(':') if ':' in coin else (coin,None)

			desc = 'chain token in metadata'
			tx.chain = metadata.pop(0).lower() if len(metadata) == 5 else 'mainnet'

			from ..protocol import CoinProtocol,init_proto
			network = CoinProtocol.Base.chain_name_to_network(tx.cfg,coin,tx.chain)

			desc = 'initialization of protocol'
			tx.proto = init_proto( tx.cfg, coin, network=network, need_amt=True )
			if tokensym:
				tx.proto.tokensym = tokensym

			desc = 'metadata (4 items)'
			txid,send_amt,tx.timestamp,blockcount = metadata

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
			desc = 'inputs data'
			tx.inputs  = eval_io_data(inputs_data,'inputs')
			desc = 'outputs data'
			tx.outputs = eval_io_data(outputs_data,'outputs')
			desc = 'send amount in metadata'
			from decimal import Decimal
			assert Decimal(send_amt) == tx.send_amt, f'{send_amt} != {tx.send_amt}'
		except Exception as e:
			die(2,f'Invalid {desc} in transaction file: {e!s}')

	def make_filename(self):
		tx = self.tx
		def gen_filename():
			yield tx.txid
			if tx.coin != 'BTC':
				yield '-' + tx.dcoin
			yield f'[{tx.send_amt!s}'
			if tx.is_replaceable():
				yield ',{}'.format(tx.fee_abs2rel(tx.fee,to_unit=tx.fn_fee_unit))
			if tx.get_serialized_locktime():
				yield f',tl={tx.get_serialized_locktime()}'
			yield ']'
			if tx.proto.testnet:
				yield '.' + tx.proto.network
			yield '.' + tx.ext
		return ''.join(gen_filename())

	def format(self):
		tx = self.tx

		def amt_to_str(d):
			return {k: (str(d[k]) if k == 'amt' else d[k]) for k in d}

		coin_id = '' if tx.coin == 'BTC' else tx.coin + ('' if tx.coin == tx.dcoin else ':'+tx.dcoin)
		lines = [
			'{}{} {} {} {} {}{}'.format(
				(coin_id+' ' if coin_id else ''),
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
			lines.append(baseconv('b58').frombytes(tx.comment.encode(),tostr=True))

		if tx.coin_txid:
			if not tx.comment:
				lines.append('-') # keep old tx files backwards compatible
			lines.append(tx.coin_txid)

		self.chksum = make_chksum_6(' '.join(lines))
		fmt_data = '\n'.join([self.chksum] + lines) + '\n'
		if len(fmt_data) > tx.cfg.max_tx_file_size:
			die( 'MaxFileSizeExceeded', f'Transaction file size exceeds limit ({tx.cfg.max_tx_file_size} bytes)' )
		return fmt_data

	def write(self,
		add_desc              = '',
		ask_write             = True,
		ask_write_default_yes = False,
		ask_tty               = True,
		ask_overwrite         = True ):

		if ask_write is False:
			ask_write_default_yes = True

		if not self.filename:
			self.filename = self.make_filename()

		if not self.fmt_data:
			self.fmt_data = self.format()

		from ..fileutil import write_data_to_file
		write_data_to_file(
			cfg                   = self.tx.cfg,
			outfile               = self.filename,
			data                  = self.fmt_data,
			desc                  = self.tx.desc + add_desc,
			ask_overwrite         = ask_overwrite,
			ask_write             = ask_write,
			ask_tty               = ask_tty,
			ask_write_default_yes = ask_write_default_yes )

	@classmethod
	def get_proto(cls,cfg,filename,quiet_open=False):
		from . import BaseTX
		tmp_tx = BaseTX(cfg=cfg)
		cls(tmp_tx).parse(filename,metadata_only=True,quiet_open=quiet_open)
		return tmp_tx.proto

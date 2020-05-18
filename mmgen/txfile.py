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
txfile.py:  Transaction file operations for the MMGen suite
"""

from .common import *
from .obj import HexStr,MMGenTxID,UnknownCoinAmt,CoinTxID,MMGenTxLabel
from .tx import MMGenTxOutput,MMGenTxOutputList,MMGenTxInput,MMGenTxInputList
from .exception import MaxFileSizeExceeded

class MMGenTxFile:

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
			assert type(d) == list,'{} data not a list!'.format(desc)
			if not (desc == 'outputs' and g.proto.base_coin == 'ETH'): # ETH txs can have no outputs
				assert len(d),'no {}!'.format(desc)
			for e in d:
				e['amt'] = g.proto.coin_amt(e['amt'])
			io,io_list = (
				(MMGenTxOutput,MMGenTxOutputList),
				(MMGenTxInput,MMGenTxInputList)
			)[desc=='inputs']
			return io_list(io(**e) for e in d)

		tx_data = get_data_from_file(infile,tx.desc+' data',quiet=quiet_open)

		try:
			desc = 'data'
			if len(tx_data) > g.max_tx_file_size:
				raise MaxFileSizeExceeded(f'Transaction file size exceeds limit ({g.max_tx_file_size} bytes)')
			tx_data = tx_data.splitlines()
			assert len(tx_data) >= 5,'number of lines less than 5'
			assert len(tx_data[0]) == 6,'invalid length of first line'
			self.chksum = HexStr(tx_data.pop(0),on_fail='raise')
			assert self.chksum == make_chksum_6(' '.join(tx_data)),'file data does not match checksum'

			if len(tx_data) == 6:
				assert len(tx_data[-1]) == 64,'invalid coin TxID length'
				desc = f'{g.proto.name} TxID'
				tx.coin_txid = CoinTxID(tx_data.pop(-1),on_fail='raise')

			if len(tx_data) == 5:
				# rough check: allow for 4-byte utf8 characters + base58 (4 * 11 / 8 = 6 (rounded up))
				assert len(tx_data[-1]) < MMGenTxLabel.max_len*6,'invalid comment length'
				c = tx_data.pop(-1)
				if c != '-':
					desc = 'encoded comment (not base58)'
					from .baseconv import baseconv
					comment = baseconv.tobytes(c,'b58').decode()
					assert comment != False,'invalid comment'
					desc = 'comment'
					tx.label = MMGenTxLabel(comment,on_fail='raise')

			desc = 'number of lines' # four required lines
			metadata,tx.hex,inputs_data,outputs_data = tx_data
			assert len(metadata) < 100,'invalid metadata length' # rough check
			metadata = metadata.split()

			if metadata[-1].startswith('LT='):
				desc = 'locktime'
				tx.locktime = int(metadata.pop()[3:])

			tx.coin = metadata.pop(0) if len(metadata) == 6 else 'BTC'
			if ':' in tx.coin:
				tx.coin,tx.dcoin = tx.coin.split(':')

			if len(metadata) == 5:
				t = metadata.pop(0)
				tx.chain = (t.lower(),None)[t=='Unknown']

			desc = 'metadata (4 items minimum required)'
			txid,send_amt,tx.timestamp,blockcount = metadata

			desc = 'txid in metadata'
			tx.txid = MMGenTxID(txid,on_fail='raise')
			desc = 'send amount in metadata'
			tx.send_amt = UnknownCoinAmt(send_amt) # temporary, for 'metadata_only'
			desc = 'block count in metadata'
			tx.blockcount = int(blockcount)

			if metadata_only:
				return

			desc = 'send amount in metadata'
			tx.send_amt = g.proto.coin_amt(send_amt,on_fail='raise')

			desc = 'transaction file hex data'
			tx.check_txfile_hex_data()
			desc = f'transaction file {tx.hexdata_type} data'
			tx.parse_txfile_hex_data()
			# the following ops will all fail if g.coin doesn't match tx.coin
			desc = 'coin type in metadata'
			assert tx.coin == g.coin, tx.coin
			desc = 'inputs data'
			tx.inputs  = eval_io_data(inputs_data,'inputs')
			desc = 'outputs data'
			tx.outputs = eval_io_data(outputs_data,'outputs')
		except Exception as e:
			die(2,f'Invalid {desc} in transaction file: {e.args[0]}')

		# is_for_chain() is no-op for Ethereum: test and mainnet addrs have same format
		if not tx.chain and not tx.inputs[0].addr.is_for_chain('testnet'):
			tx.chain = 'mainnet'

		if tx.dcoin:
			tx.resolve_g_token_from_txfile()
			g.proto.dcoin = tx.dcoin

	def make_filename(self):
		tx = self.tx
		def gen_filename():
			yield tx.txid
			if g.coin != 'BTC':
				yield '-' + g.dcoin
			yield f'[{tx.send_amt!s}'
			if tx.is_replaceable():
				yield ',{}'.format(tx.fee_abs2rel(tx.get_fee(),to_unit=tx.fn_fee_unit))
			if tx.get_hex_locktime():
				yield ',tl={}'.format(tx.get_hex_locktime())
			yield ']'
			if g.debug_utf8:
				yield '-α'
			if g.proto.testnet:
				yield '.testnet'
			yield '.' + tx.ext
		return ''.join(gen_filename())

	def format(self):
		tx = self.tx
		tx.inputs.check_coin_mismatch()
		tx.outputs.check_coin_mismatch()

		def amt_to_str(d):
			return {k: (str(d[k]) if k == 'amt' else d[k]) for k in d}

		coin_id = '' if g.coin == 'BTC' else g.coin + ('' if g.coin == g.dcoin else ':'+g.dcoin)
		lines = [
			'{}{} {} {} {} {}{}'.format(
				(coin_id+' ' if coin_id else ''),
				tx.chain.upper() if tx.chain else 'Unknown',
				tx.txid,
				tx.send_amt,
				tx.timestamp,
				tx.blockcount,
				('',' LT={}'.format(tx.locktime))[bool(tx.locktime)]
			),
			tx.hex,
			ascii([amt_to_str(e.__dict__) for e in tx.inputs]),
			ascii([amt_to_str(e.__dict__) for e in tx.outputs])
		]

		if tx.label:
			from .baseconv import baseconv
			lines.append(baseconv.frombytes(tx.label.encode(),'b58',tostr=True))

		if tx.coin_txid:
			if not tx.label:
				lines.append('-') # keep old tx files backwards compatible
			lines.append(tx.coin_txid)

		self.chksum = make_chksum_6(' '.join(lines))
		fmt_data = '\n'.join([self.chksum] + lines) + '\n'
		if len(fmt_data) > g.max_tx_file_size:
			raise MaxFileSizeExceeded(f'Transaction file size exceeds limit ({g.max_tx_file_size} bytes)')
		return fmt_data

	def write(self,
		add_desc              = '',
		ask_write             = True,
		ask_write_default_yes = False,
		ask_tty               = True,
		ask_overwrite         = True ):

		if ask_write == False:
			ask_write_default_yes = True

		if not self.filename:
			self.filename = self.make_filename()

		if not self.fmt_data:
			self.fmt_data = self.format()

		write_data_to_file(
			outfile               = self.filename,
			data                  = self.fmt_data,
			desc                  = self.tx.desc + add_desc,
			ask_overwrite         = ask_overwrite,
			ask_write             = ask_write,
			ask_tty               = ask_tty,
			ask_write_default_yes = ask_write_default_yes )

#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.btc.tx.base: Bitcoin base transaction class
"""

from collections import namedtuple

from ....tx import base as TxBase
from ....obj import MMGenList, HexStr
from ....util import msg, make_chksum_6, die, pp_fmt

def addr2scriptPubKey(proto, addr):

	def decode_addr(proto, addr):
		ap = proto.decode_addr(addr)
		assert ap, f'coin address {addr!r} could not be parsed'
		return ap.bytes.hex()

	return {
		'p2pkh': '76a914' + decode_addr(proto, addr) + '88ac',
		'p2sh':  'a914' + decode_addr(proto, addr) + '87',
		'bech32': proto.witness_vernum_hex + '14' + decode_addr(proto, addr)
	}[addr.addr_fmt]

def scriptPubKey2addr(proto, s):
	if len(s) == 50 and s[:6] == '76a914' and s[-4:] == '88ac':
		return proto.pubhash2addr(bytes.fromhex(s[6:-4]), 'p2pkh'), 'p2pkh'
	elif len(s) == 46 and s[:4] == 'a914' and s[-2:] == '87':
		return proto.pubhash2addr(bytes.fromhex(s[4:-2]), 'p2sh'), 'p2sh'
	elif len(s) == 44 and s[:4] == proto.witness_vernum_hex + '14':
		return proto.pubhash2bech32addr(bytes.fromhex(s[4:])), 'bech32'
	else:
		raise NotImplementedError(f'Unknown scriptPubKey ({s})')

def DeserializeTX(proto, txhex):
	"""
	Parse a serialized Bitcoin transaction
	For checking purposes, additionally reconstructs the serialized TX without signature
	"""

	def bytes2int(bytes_le):
		return int(bytes_le[::-1].hex(), 16)

	def bytes2coin_amt(bytes_le):
		return proto.coin_amt(bytes2int(bytes_le), from_unit='satoshi')

	def bshift(n, skip=False, sub_null=False):
		nonlocal idx, raw_tx
		ret = tx[idx:idx+n]
		idx += n
		if sub_null:
			raw_tx += b'\x00'
		elif not skip:
			raw_tx += ret
		return ret

	# https://bitcoin.org/en/developer-reference#compactsize-unsigned-integers
	# For example, the number 515 is encoded as 0xfd0302.
	def readVInt(skip=False):
		nonlocal idx, raw_tx
		s = tx[idx]
		idx += 1
		if not skip:
			raw_tx.append(s)

		vbytes_len = 1 if s < 0xfd else 2 if s == 0xfd else 4 if s == 0xfe else 8

		if vbytes_len == 1:
			return s
		else:
			vbytes = tx[idx:idx+vbytes_len]
			idx += vbytes_len
			if not skip:
				raw_tx += vbytes
			return int(vbytes[::-1].hex(), 16)

	def make_txid(tx_bytes):
		from hashlib import sha256
		return sha256(sha256(tx_bytes).digest()).digest()[::-1].hex()

	tx = bytes.fromhex(txhex)
	raw_tx = bytearray()
	idx = 0

	d = {'version': bytes2int(bshift(4))}

	if d['version'] > 0x7fffffff: # version is signed integer
		die(3, f"{d['version']}: transaction version greater than maximum allowed value (int32_t)!")

	has_witness = tx[idx] == 0
	if has_witness:
		u = bshift(2, skip=True).hex()
		if u != '0001':
			die('IllegalWitnessFlagValue', f'{u!r}: Illegal value for flag in transaction!')

	d['num_txins'] = readVInt()

	d['txins'] = MMGenList([{
		'txid':      bshift(32)[::-1].hex(),
		'vout':      bytes2int(bshift(4)),
		'scriptSig': bshift(readVInt(skip=True), sub_null=True).hex(),
		'nSeq':      bshift(4)[::-1].hex()
	} for i in range(d['num_txins'])])

	d['num_txouts'] = readVInt()

	d['txouts'] = MMGenList([{
		'amt':          bytes2coin_amt(bshift(8)),
		'scriptPubKey': bshift(readVInt()).hex()
	} for i in range(d['num_txouts'])])

	for o in d['txouts']:
		o['address'] = scriptPubKey2addr(proto, o['scriptPubKey'])[0]

	if has_witness:
		# https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki
		# A non-witness program (defined hereinafter) txin MUST be associated with an empty
		# witness field, represented by a 0x00.

		d['txid'] = make_txid(tx[:4] + tx[6:idx] + tx[-4:])
		d['witness_size'] = len(tx) - idx + 2 - 4 # add len(marker+flag), subtract len(locktime)

		for txin in d['txins']:
			if tx[idx] == 0:
				bshift(1, skip=True)
				continue
			txin['witness'] = [
				bshift(readVInt(skip=True), skip=True).hex() for item in range(readVInt(skip=True))]
	else:
		d['txid'] = make_txid(tx)
		d['witness_size'] = 0

	if len(tx) - idx != 4:
		die('TxHexParseError', 'TX hex has invalid length: {} extra bytes'.format(len(tx)-idx-4))

	d['locktime'] = bytes2int(bshift(4))
	d['unsigned_hex'] = raw_tx.hex()

	return namedtuple('deserialized_tx', list(d.keys()))(**d)

class Base(TxBase.Base):
	rel_fee_desc = 'satoshis per byte'
	rel_fee_disp = 'sat/byte'
	_deserialized = None

	class InputList(TxBase.Base.InputList):

		# Lexicographical Indexing of Transaction Inputs and Outputs
		# https://github.com/bitcoin/bips/blob/master/bip-0069.mediawiki
		def sort_bip69(self):
			def sort_func(a):
				return (
					bytes.fromhex(a.txid)
					+ int.to_bytes(a.vout, 4, 'big'))
			self.sort(key=sort_func)

	class OutputList(TxBase.Base.OutputList):

		def sort_bip69(self):
			def sort_func(a):
				return (
					int.to_bytes(a.amt.to_unit('satoshi'), 8, 'big')
					+ bytes.fromhex(addr2scriptPubKey(self.parent.proto, a.addr)))
			self.sort(key=sort_func)

	def has_segwit_inputs(self):
		return any(i.mmtype in ('S', 'B') for i in self.inputs)

	def has_segwit_outputs(self):
		return any(o.mmtype in ('S', 'B') for o in self.outputs)

	# https://bitcoin.stackexchange.com/questions/1195/how-to-calculate-transaction-size-before-sending
	# 180: uncompressed, 148: compressed
	def estimate_size_old(self):
		if not self.inputs or not self.outputs:
			return None
		return len(self.inputs)*180 + len(self.outputs)*34 + 10

	# https://bitcoincore.org/en/segwit_wallet_dev/
	# vsize: 3 times of the size with original serialization, plus the size with new
	# serialization, divide the result by 4 and round up to the next integer.

	# TODO: results differ slightly from actual transaction size
	def estimate_size(self):
		if not self.inputs or not self.outputs:
			return None

		sig_size = 72 # sig in DER format
		pubkey_size_uncompressed = 65
		pubkey_size_compressed = 33

		def get_inputs_size():
			# txid vout [scriptSig size (vInt)] scriptSig (<sig> <pubkey>) nSeq
			isize_common = 32 + 4 + 1 + 4 # txid vout [scriptSig size] nSeq = 41
			input_size = {
				'L': isize_common + sig_size + pubkey_size_uncompressed, # = 180
				'C': isize_common + sig_size + pubkey_size_compressed,   # = 148
				'S': isize_common + 23,                                  # = 64
				'B': isize_common + 0                                    # = 41
			}
			ret = sum(input_size[i.mmtype] for i in self.inputs if i.mmtype)

			# We have no way of knowing whether a non-MMGen P2PKH addr is compressed or uncompressed
			# until we see the key, so assume compressed for fee-estimation purposes. If fee estimate
			# is off by more than 5%, sign() aborts and user is instructed to use --vsize-adj option.
			return ret + sum(input_size['C'] for i in self.inputs if not i.mmtype)

		def get_outputs_size():
			# output bytes = amt: 8, byte_count: 1+, pk_script
			# pk_script bytes: p2pkh: 25, p2sh: 23, bech32: 22
			return sum({'p2pkh':34, 'p2sh':32, 'bech32':31}[o.addr.addr_fmt] for o in self.outputs)

		# https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki
		# The witness is a serialization of all witness data of the transaction. Each txin is
		# associated with a witness field. A witness field starts with a var_int to indicate the
		# number of stack items for the txin. It is followed by stack items, with each item starts
		# with a var_int to indicate the length. Witness data is NOT script.

		# A non-witness program txin MUST be associated with an empty witness field, represented
		# by a 0x00. If all txins are not witness program, a transaction's wtxid is equal to its txid.
		def get_witness_size():
			if not self.has_segwit_inputs():
				return 0
			wf_size = 1 + 1 + sig_size + 1 + pubkey_size_compressed # vInt vInt sig vInt pubkey = 108
			return sum((1, wf_size)[i.mmtype in ('S', 'B')] for i in self.inputs)

		isize = get_inputs_size()
		osize = get_outputs_size()
		wsize = get_witness_size()

		# TODO: compute real varInt sizes instead of assuming 1 byte
		# Serialization:
		#   old:     [nVersion]              [vInt][txins][vInt][txouts]         [nLockTime]
		old_size =   4                     + 1   + isize + 1  + osize          + 4
		#   marker = 0x00, flag = 0x01
		#   new:     [nVersion][marker][flag][vInt][txins][vInt][txouts][witness][nLockTime]
		new_size =   4       + 1     + 1   + 1   + isize + 1  + osize + wsize  + 4 if wsize else old_size

		ret = (old_size * 3 + new_size) // 4

		self.cfg._util.dmsg(
			'\nData from estimate_size():\n' +
			f'  inputs size: {isize}, outputs size: {osize}, witness size: {wsize}\n' +
			f'  size: {new_size}, vsize: {ret}, old_size: {old_size}')

		return int(ret * (self.cfg.vsize_adj or 1))

	# convert absolute CoinAmt fee to sat/byte for display using estimated size
	def fee_abs2rel(self, abs_fee, to_unit='satoshi'):
		return str(int(
			abs_fee /
			getattr(self.proto.coin_amt, to_unit) /
			self.estimate_size()))

	@property
	def deserialized(self):
		if not self._deserialized:
			self._deserialized = DeserializeTX(self.proto, self.serialized)
		return self._deserialized

	def update_serialized(self, data):
		self.serialized = HexStr(data)
		self._deserialized = None
		self.check_serialized_integrity()

	def check_serialized_integrity(self):
		"""
		Check that a malicious, compromised or malfunctioning coin daemon hasn't produced bad
		serialized tx data.

		Does not check witness data.

		Perform this check every time a serialized tx is received from the coin daemon or read
		from a transaction file.
		"""

		def do_error(errmsg):
			die('TxHexMismatch', errmsg+'\n'+hdr)

		def check_equal(desc, hexio, mmio):
			if mmio != hexio:
				msg('\nMMGen {d}:\n{m}\nSerialized {d}:\n{h}'.format(
					d = desc,
					m = pp_fmt(mmio),
					h = pp_fmt(hexio)))
				do_error(
					f'{desc.capitalize()} in serialized transaction data from coin daemon ' +
					'do not match those in MMGen transaction!')

		hdr = 'A malicious or malfunctioning coin daemon or other program may have altered your data!'

		dtx = self.deserialized

		if dtx.locktime != int(self.locktime or 0):
			do_error(
				f'Transaction hex nLockTime ({dtx.locktime}) ' +
				f'does not match MMGen transaction nLockTime ({self.locktime})')

		check_equal(
			'sequence numbers',
			[i['nSeq'] for i in dtx.txins],
			['{:08x}'.format(i.sequence or self.proto.max_int) for i in self.inputs])

		check_equal(
			'inputs',
			sorted((i['txid'], i['vout']) for i in dtx.txins),
			sorted((i.txid, i.vout) for i in self.inputs))

		check_equal(
			'outputs',
			sorted((o['address'], o['amt']) for o in dtx.txouts),
			sorted((o.addr, o.amt) for o in self.outputs))

		if str(self.txid) != make_chksum_6(bytes.fromhex(dtx.unsigned_hex)).upper():
			do_error(f'MMGen TxID ({self.txid}) does not match serialized transaction data!')

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
altcoins.eth.tx: Ethereum transaction classes for the MMGen suite
"""

import json
from mmgen.common import *
from mmgen.obj import *

from mmgen.tx import MMGenTX,MMGenBumpTX,MMGenSplitTX

class EthereumMMGenTX(MMGenTX):
	desc = 'Ethereum transaction'
	contract_desc = 'contract'
	tx_gas = ETHAmt(21000,'wei')    # an approximate number, used for fee estimation purposes
	start_gas = ETHAmt(21000,'wei') # the actual startgas amt used in the transaction
									# for simple sends with no data, tx_gas = start_gas = 21000
	fee_fail_fs = 'Network fee estimation failed'
	no_chg_msg = 'Warning: Transaction leaves account with zero balance'
	rel_fee_desc = 'gas price'
	rel_fee_disp = 'gas price in Gwei'
	txview_hdr_fs = 'TRANSACTION DATA\n\nID={i} ({a} {c}) UTC={t} Sig={s} Locktime={l}\n'
	txview_hdr_fs_short = 'TX {i} ({a} {c}) UTC={t} Sig={s} Locktime={l}\n'
	txview_ftr_fs = 'Total in account: {i} {d}\nTotal to spend:   {o} {d}\nTX fee:           {a} {c}{r}\n'
	txview_ftr_fs_short = 'In {i} {d} - Out {o} {d}\nFee {a} {c}{r}\n'
	fmt_keys = ('from','to','amt','nonce')
	usr_fee_prompt = 'Enter transaction fee or gas price: '
	fn_fee_unit = 'Mwei'
	usr_rel_fee = None # not in MMGenTX
	disable_fee_check = False
	txobj  = None # ""
	usr_contract_data = HexStr('')

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		if hasattr(opt,'tx_gas') and opt.tx_gas:
			self.tx_gas = self.start_gas = ETHAmt(int(opt.tx_gas),'wei')
		if hasattr(opt,'contract_data') and opt.contract_data:
			m = "'--contract-data' option may not be used with token transaction"
			assert not 'Token' in type(self).__name__, m
			self.usr_contract_data = HexStr(open(opt.contract_data).read().strip())
			self.disable_fee_check = True

	@classmethod
	def get_exec_status(cls,txid,silent=False):
		d = g.rpc.eth_getTransactionReceipt('0x'+txid)
		if not silent:
			if 'contractAddress' in d and d['contractAddress']:
				msg('Contract address: {}'.format(d['contractAddress'].replace('0x','')))
		return int(d['status'],16)

	def is_replaceable(self): return True

	def get_fee_from_tx(self):
		return self.fee

	def check_fee(self):
		assert self.disable_fee_check or (self.fee <= g.proto.max_tx_fee)

	def get_hex_locktime(self): return None # TODO

	def check_pubkey_scripts(self): pass

	def check_sigs(self,deserial_tx=None):
		if is_hex_str(self.hex):
			self.mark_signed()
			return True
		return False

	# hex data if signed, json if unsigned
	def check_txfile_hex_data(self):
		if self.check_sigs():
			from .pyethereum.transactions import Transaction
			from . import rlp
			etx = rlp.decode(bytes.fromhex(self.hex),Transaction)
			d = etx.to_dict() # ==> hex values have '0x' prefix, 0 is '0x'
			for k in ('sender','to','data'):
				if k in d: d[k] = d[k].replace('0x','',1)
			o = {   'from':     CoinAddr(d['sender']),
					'to':       CoinAddr(d['to']) if d['to'] else Str(''), # NB: for token, 'to' is token address
					'amt':      ETHAmt(d['value'],'wei'),
					'gasPrice': ETHAmt(d['gasprice'],'wei'),
					'startGas': ETHAmt(d['startgas'],'wei'),
					'nonce':    ETHNonce(d['nonce']),
					'data':     HexStr(d['data']) }
			if o['data'] and not o['to']: # token- or contract-creating transaction
				o['token_addr'] = TokenAddr(etx.creates.hex()) # NB: could be a non-token contract address
				self.disable_fee_check = True
			txid = CoinTxID(etx.hash.hex())
			assert txid == self.coin_txid,"txid in tx.hex doesn't match value in MMGen transaction file"
		else:
			d = json.loads(self.hex)
			o = {   'from':     CoinAddr(d['from']),
					'to':       CoinAddr(d['to']) if d['to'] else Str(''), # NB: for token, 'to' is sendto address
					'amt':      ETHAmt(d['amt']),
					'gasPrice': ETHAmt(d['gasPrice']),
					'startGas': ETHAmt(d['startGas']),
					'nonce':    ETHNonce(d['nonce']),
					'chainId':  Int(d['chainId']),
					'data':     HexStr(d['data']) }
		self.tx_gas = o['startGas'] # approximate, but better than nothing
		self.fee = self.fee_rel2abs(o['gasPrice'].toWei())
		self.txobj = o
		return d # 'token_addr','decimals' required by Token subclass

	def get_nonce(self):
		return ETHNonce(int(g.rpc.parity_nextNonce('0x'+self.inputs[0].addr),16))

	def make_txobj(self): # called by create_raw()
		chain_id_method = ('parity_chainId','eth_chainId')['eth_chainId' in g.rpc.caps]
		self.txobj = {
			'from': self.inputs[0].addr,
			'to':   self.outputs[0].addr if self.outputs else Str(''),
			'amt':  self.outputs[0].amt if self.outputs else ETHAmt('0'),
			'gasPrice': self.usr_rel_fee or self.fee_abs2rel(self.fee,to_unit='eth'),
			'startGas': self.start_gas,
			'nonce': self.get_nonce(),
			'chainId': Int(g.rpc.request(chain_id_method),16),
			'data':  self.usr_contract_data,
		}

	# Instead of serializing tx data as with BTC, just create a JSON dump.
	# This complicates things but means we avoid using the rlp library to deserialize the data,
	# thus removing an attack vector
	def create_raw(self):
		assert len(self.inputs) == 1,'Transaction has more than one input!'
		o_num = len(self.outputs)
		o_ok = 0 if self.usr_contract_data else 1
		assert o_num == o_ok,'Transaction has {} output{} (should have {})'.format(o_num,suf(o_num),o_ok)
		self.make_txobj()
		odict = { k: str(v) for k,v in self.txobj.items() if k != 'token_to' }
		self.hex = json.dumps(odict)
		self.update_txid()

	def del_output(self,idx):
		pass

	def update_txid(self):
		assert not is_hex_str(self.hex),'update_txid() must be called only when self.hex is not hex data'
		self.txid = MMGenTxID(make_chksum_6(self.hex).upper())

	def get_blockcount(self):
		return Int(g.rpc.eth_blockNumber(),16)

	def process_cmd_args(self,cmd_args,ad_f,ad_w):
		lc = len(cmd_args)
		if lc == 0 and self.usr_contract_data and not 'Token' in type(self).__name__:
			return
		if lc != 1:
			fs = '{} output{} specified, but Ethereum transactions must have exactly one'
			die(1,fs.format(lc,suf(lc)))

		for a in cmd_args:
			self.process_cmd_arg(a,ad_f,ad_w)

	def select_unspent(self,unspent):
		prompt = 'Enter an account to spend from: '
		while True:
			reply = my_raw_input(prompt).strip()
			if reply:
				if not is_int(reply):
					msg('Account number must be an integer')
				elif int(reply) < 1:
					msg('Account number must be >= 1')
				elif int(reply) > len(unspent):
					msg('Account number must be <= {}'.format(len(unspent)))
				else:
					return [int(reply)]

	# coin-specific fee routines:
	def get_relay_fee(self): return ETHAmt('0') # TODO

	# given absolute fee in ETH, return gas price in Gwei using tx_gas
	def fee_abs2rel(self,abs_fee,to_unit='Gwei'):
		ret = ETHAmt(int(abs_fee.toWei() // self.tx_gas.toWei()),'wei')
		dmsg('fee_abs2rel() ==> {} ETH'.format(ret))
		return ret if to_unit == 'eth' else ret.to_unit(to_unit,show_decimal=True)

	# get rel_fee (gas price) from network, return in native wei
	def get_rel_fee_from_network(self):
		return Int(g.rpc.eth_gasPrice(),16),'eth_gasPrice' # ==> rel_fee,fe_type

	# given rel fee and units, return absolute fee using tx_gas
	def convert_fee_spec(self,foo,units,amt,unit):
		self.usr_rel_fee = ETHAmt(int(amt),units[unit])
		return ETHAmt(self.usr_rel_fee.toWei() * self.tx_gas.toWei(),'wei')

	# given rel fee in wei, return absolute fee using tx_gas (not in MMGenTX)
	def fee_rel2abs(self,rel_fee):
		assert isinstance(rel_fee,int),"'{}': incorrect type for fee estimate (not an integer)".format(rel_fee)
		return ETHAmt(rel_fee * self.tx_gas.toWei(),'wei')

	# given fee estimate (gas price) in wei, return absolute fee, adjusting by opt.tx_fee_adj
	def fee_est2abs(self,rel_fee,fe_type=None):
		ret = self.fee_rel2abs(rel_fee) * opt.tx_fee_adj
		if opt.verbose:
			msg('Estimated fee: {} ETH'.format(ret))
		return ret

	def convert_and_check_fee(self,tx_fee,desc='Missing description'):
		abs_fee = self.process_fee_spec(tx_fee,None,on_fail='return')
		if abs_fee == False:
			return False
		elif not self.disable_fee_check and (abs_fee > g.proto.max_tx_fee):
			m = '{} {c}: {} fee too large (maximum fee: {} {c})'
			msg(m.format(abs_fee.hl(),desc,g.proto.max_tx_fee.hl(),c=g.coin))
			return False
		else:
			return abs_fee

	def update_change_output(self,change_amt):
		if self.outputs and self.outputs[0].is_chg:
			self.update_output_amt(0,ETHAmt(change_amt))

	def update_send_amt(self,foo):
		if self.outputs:
			self.send_amt = self.outputs[0].amt

	def format_view_body(self,blockcount,nonmm_str,max_mmwid,enl,terse,sort):
		m = {}
		for k in ('inputs','outputs'):
			if len(getattr(self,k)):
				m[k] = getattr(self,k)[0].mmid if len(getattr(self,k)) else ''
				m[k] = ' ' + m[k].hl() if m[k] else ' ' + MMGenID.hlc(nonmm_str)
		fs = """From:      {}{f_mmid}
				To:        {}{t_mmid}
				Amount:    {} {c}
				Gas price: {g} Gwei
				Start gas: {G} Kwei
				Nonce:     {}
				Data:      {d}
				\n""".replace('\t','')
		ld = len(self.txobj['data'])
		return fs.format(   *((self.txobj[k] if self.txobj[k] != '' else Str('None')).hl() for k in self.fmt_keys),
							d='{}... ({} bytes)'.format(self.txobj['data'][:40],ld//2) if ld else Str('None'),
							c=g.dcoin if len(self.outputs) else '',
							g=yellow(str(self.txobj['gasPrice'].to_unit('Gwei',show_decimal=True))),
							G=yellow(str(self.txobj['startGas'].toKwei())),
							t_mmid=m['outputs'] if len(self.outputs) else '',
							f_mmid=m['inputs'])

	def format_view_abs_fee(self):
		fee = self.fee_rel2abs(self.txobj['gasPrice'].toWei())
		note = ' (max)' if self.txobj['data'] else ''
		return fee.hl() + note

	def format_view_rel_fee(self,terse): return ''
	def format_view_verbose_footer(self): return '' # TODO

	def resolve_g_token_from_tx_file(self):
		die(2,"The '--token' option must be specified for token transaction files")

	def final_inputs_ok_msg(self,change_amt):
		m = "Transaction leaves {} {} in the sender's account"
		chg = '0' if (self.outputs and self.outputs[0].is_chg) else change_amt
		return m.format(ETHAmt(chg).hl(),g.coin)

	def do_sign(self,wif,tx_num_str):
		o = self.txobj
		o_conv = {
			'to':       bytes.fromhex(o['to']),
			'startgas': o['startGas'].toWei(),
			'gasprice': o['gasPrice'].toWei(),
			'value':    o['amt'].toWei() if o['amt'] else 0,
			'nonce':    o['nonce'],
			'data':     bytes.fromhex(o['data']) }

		from .pyethereum.transactions import Transaction
		etx = Transaction(**o_conv).sign(wif,o['chainId'])
		assert etx.sender.hex() == o['from'],(
			'Sender address recovered from signature does not match true sender')

		from . import rlp
		self.hex = rlp.encode(etx).hex()
		self.coin_txid = CoinTxID(etx.hash.hex())

		if o['data']:
			if o['to']:
				assert self.txobj['token_addr'] == TokenAddr(etx.creates.hex()),'Token address mismatch'
			else: # token- or contract-creating transaction
				self.txobj['token_addr'] = TokenAddr(etx.creates.hex())

		assert self.check_sigs(),'Signature check failed'

	def sign(self,tx_num_str,keys): # return True or False; don't exit or raise exception

		if self.marked_signed():
			msg('Transaction is already signed!')
			return False

		if not self.check_correct_chain(on_fail='return'):
			return False

		msg_r('Signing transaction{}...'.format(tx_num_str))

		try:
			self.do_sign(keys[0].sec.wif,tx_num_str)
			msg('OK')
			return True
		except Exception as e:
			m = "{!r}: transaction signing failed!"
			msg(m.format(e.args[0]))
			if g.traceback:
				import traceback
				ymsg('\n'+''.join(traceback.format_exception(*sys.exc_info())))
			return False

	def get_status(self,status=False):

		class r(object): pass

		def is_in_mempool():
			if not 'full_node' in g.rpc.caps:
				return False
			return '0x'+self.coin_txid in [x['hash'] for x in g.rpc.parity_pendingTransactions()]

		def is_in_wallet():
			d = g.rpc.eth_getTransactionReceipt('0x'+self.coin_txid)
			if d and 'blockNumber' in d and d['blockNumber'] is not None:
				r.confs = 1 + int(g.rpc.eth_blockNumber(),16) - int(d['blockNumber'],16)
				r.exec_status = int(d['status'],16)
				return True
			return False

		if is_in_mempool():
			msg('Transaction is in mempool' if status else 'Warning: transaction is in mempool!')
			return

		if status:
			if is_in_wallet():
				if self.txobj['data']:
					cd = capfirst(self.contract_desc)
					if r.exec_status == 0:
						msg('{} failed to execute!'.format(cd))
					else:
						msg('{} successfully executed with status {}'.format(cd,r.exec_status))
				die(0,'Transaction has {} confirmation{}'.format(r.confs,suf(r.confs)))
			die(1,'Transaction is neither in mempool nor blockchain!')

	def send(self,prompt_user=True,exit_on_fail=False):

		if not self.marked_signed():
			die(1,'Transaction is not signed!')

		self.check_correct_chain(on_fail='die')

		fee = self.fee_rel2abs(self.txobj['gasPrice'].toWei())

		if not self.disable_fee_check and (fee > g.proto.max_tx_fee):
			die(2,'Transaction fee ({}) greater than {} max_tx_fee ({} {})!'.format(
				fee,g.proto.name.capitalize(),g.proto.max_tx_fee,g.coin))

		self.get_status()

		if prompt_user:
			self.confirm_send()

		ret = None if g.bogus_send else g.rpc.eth_sendRawTransaction('0x'+self.hex,on_fail='return')

		from mmgen.rpc import rpc_error,rpc_errmsg
		if rpc_error(ret):
			msg(yellow(rpc_errmsg(ret)))
			msg(red('Send of MMGen transaction {} failed'.format(self.txid)))
			if exit_on_fail:
				sys.exit(1)
			return False
		else:
			if g.bogus_send:
				m = 'BOGUS transaction NOT sent: {}'
			else:
				m = 'Transaction sent: {}'
				assert ret == '0x'+self.coin_txid,'txid mismatch (after sending)'
			self.desc = 'sent transaction'
			msg(m.format(self.coin_txid.hl()))
			self.add_timestamp()
			self.add_blockcount()
			return True

	def get_cmdline_input_addrs(self):
		ret = []
		if opt.inputs:
			from mmgen.tw import TrackingWallet
			r = TrackingWallet().data_root # must create new instance here
			m = 'Address {!r} not in tracking wallet'
			for i in opt.inputs.split(','):
				if is_mmgen_id(i):
					for addr in r:
						if r[addr]['mmid'] == i:
							ret.append(addr)
							break
					else:
						raise UserAddressNotInWallet(m.format(i))
				elif is_coin_addr(i):
					if not i in r:
						raise UserAddressNotInWallet(m.format(i))
					ret.append(i)
				else:
					die(1,"'{}': not an MMGen ID or coin address".format(i))
		return ret

	def print_contract_addr(self):
		if 'token_addr' in self.txobj:
			msg('Contract address: {}'.format(self.txobj['token_addr'].hl()))

class EthereumTokenMMGenTX(EthereumMMGenTX):
	desc = 'Ethereum token transaction'
	contract_desc = 'token contract'
	tx_gas = ETHAmt(52000,'wei')
	start_gas = ETHAmt(60000,'wei')
	fmt_keys = ('from','token_to','amt','nonce')
	fee_is_approximate = True

	def __init__(self,*args,**kwargs):
		if not kwargs.get('offline'):
			from mmgen.tw import TrackingWallet
			self.decimals = TrackingWallet().get_param('decimals')
			from .contract import Token
			self.token_obj = Token(g.token,self.decimals)
		EthereumMMGenTX.__init__(self,*args,**kwargs)

	def update_change_output(self,change_amt):
		if self.outputs[0].is_chg:
			self.update_output_amt(0,self.inputs[0].amt)

	# token transaction, so check both eth and token balances
	# TODO: add test with insufficient funds
	def precheck_sufficient_funds(self,inputs_sum,sel_unspent):
		eth_bal = self.twuo.wallet.get_eth_balance(sel_unspent[0].addr)
		if eth_bal == 0: # we don't know the fee yet
			msg('This account has no ether to pay for the transaction fee!')
			return False
		return super().precheck_sufficient_funds(inputs_sum,sel_unspent)

	def final_inputs_ok_msg(self,change_amt):
		token_bal   = ( ETHAmt('0') if self.outputs[0].is_chg else
						self.inputs[0].amt - self.outputs[0].amt )
		m = "Transaction leaves ≈{} {} and {} {} in the sender's account"
		return m.format( change_amt.hl(), g.coin, token_bal.hl(), g.dcoin )

	def get_change_amt(self): # here we know the fee
		eth_bal = self.twuo.wallet.get_eth_balance(self.inputs[0].addr)
		return eth_bal - self.fee

	def resolve_g_token_from_tx_file(self):
		g.dcoin = self.dcoin
		if is_hex_str(self.hex): return # for txsend we can leave g.token uninitialized
		d = json.loads(self.hex)
		if g.token.upper() == self.dcoin:
			g.token = d['token_addr']
		elif g.token != d['token_addr']:
			m1 = "'{p}': invalid --token parameter for {t} {n} token transaction file\n"
			m2 = "Please use '--token={t}'"
			die(1,(m1+m2).format(p=g.token,t=self.dcoin,n=capfirst(g.proto.name)))

	def make_txobj(self): # called by create_raw()
		super().make_txobj()
		t = self.token_obj
		o = self.txobj
		o['token_addr'] = t.addr
		o['decimals'] = t.decimals()
		o['token_to'] = o['to']
		o['data'] = t.create_data(o['token_to'],o['amt'])

	def check_txfile_hex_data(self):
		d = super().check_txfile_hex_data()
		o = self.txobj

		if self.check_sigs(): # online, from rlp and wallet
			o['token_addr'] = TokenAddr(o['to'])
			o['decimals'] = self.decimals
		else:                 # offline, from json
			o['token_addr'] = TokenAddr(d['token_addr'])
			o['decimals'] = Int(d['decimals'])

		from .contract import Token
		t = self.token_obj = Token(o['token_addr'],o['decimals'])

		if self.check_sigs(): # online, from rlp - 'amt' was eth amt, now token amt
			o['amt'] = t.transferdata2amt(o['data'])
		else:                 # offline, from json - 'amt' is token amt
			o['data'] = t.create_data(o['to'],o['amt'])

		o['token_to'] = type(t).transferdata2sendaddr(o['data'])

	def format_view_body(self,*args,**kwargs):
		return 'Token:     {d} {c}\n{r}'.format(
			d=self.txobj['token_addr'].hl(),
			c=blue('(' + g.dcoin + ')'),
			r=super().format_view_body(*args,**kwargs))

	def do_sign(self,wif,tx_num_str):
		o = self.txobj
		t = self.token_obj
		tx_in = t.make_tx_in(o['from'],o['to'],o['amt'],self.start_gas,o['gasPrice'],nonce=o['nonce'])
		(self.hex,self.coin_txid) = t.txsign(tx_in,wif,o['from'],chain_id=o['chainId'])
		assert self.check_sigs(),'Signature check failed'

class EthereumMMGenBumpTX(EthereumMMGenTX,MMGenBumpTX):

	def choose_output(self): pass

	def set_min_fee(self):
		self.min_fee = ETHAmt(self.fee * Decimal('1.101'))

	def update_fee(self,foo,fee):
		self.fee = fee

	def get_nonce(self):
		return self.txobj['nonce']

class EthereumTokenMMGenBumpTX(EthereumTokenMMGenTX,EthereumMMGenBumpTX): pass
class EthereumMMGenSplitTX(MMGenSplitTX): pass

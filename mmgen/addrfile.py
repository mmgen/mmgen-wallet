#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
addrfile: Address and password file classes for the MMGen suite
"""

from .util import msg,qmsg,qmsg_r,die,capfirst
from .protocol import init_proto
from .obj import MMGenObject,TwComment,WalletPassword,MMGenPWIDString
from .seed import SeedID,is_seed_id
from .key import PrivKey
from .addr import ViewKey,AddrListID,MMGenAddrType,MMGenPasswordType,is_addr_idx
from .addrlist import KeyList,AddrListData,dmsg_sc

class AddrFile(MMGenObject):
	desc        = 'addresses'
	ext         = 'addrs'
	line_ctr    = 0
	file_header = """
# {pnm} address file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
# A text label of {n} screen cells or less may be added to the right of each
# address, and it will be appended to the tracking wallet label upon import.
# The label may contain any printable ASCII symbol.
"""

	def __init__(self,parent):

		self.parent = parent
		self.infile = None

	def encrypt(self):
		from .crypto import mmgen_encrypt,mmenc_ext
		from .globalvars import g
		self.fmt_data = mmgen_encrypt(
			data = self.fmt_data.encode(),
			desc = f'new {self.parent.desc} list' )
		self.ext += f'.{mmenc_ext}'

	@property
	def filename(self):
		from .globalvars import g
		return '{}{x}{}.{}'.format(
			self.parent.id_str,
			('.' + self.parent.proto.network) if self.parent.proto.testnet else '',
			self.ext,
			x = '-α' if g.debug_utf8 else '' )

	def write(self,fn=None,ask_tty=True,ask_write_default_yes=False,binary=False,desc=None):
		from .opts import opt
		from .fileutil import write_data_to_file
		write_data_to_file(
			fn or self.filename,
			self.fmt_data,
			desc or self.desc,
			ask_tty = self.parent.has_keys and not opt.quiet,
			binary = binary )

	def make_label(self):
		p = self.parent
		bc,mt = p.proto.base_coin,p.al_id.mmtype
		l_coin = [] if bc == 'BTC' else [p.proto.coin] if bc == 'ETH' else [bc]
		l_type = [] if mt == 'E' or (mt == 'L' and not p.proto.testnet) else [mt.name.upper()]
		l_tn   = [] if not p.proto.testnet else [p.proto.network.upper()]
		lbl_p2 = ':'.join(l_coin+l_type+l_tn)
		return p.al_id.sid + ('',' ')[bool(lbl_p2)] + lbl_p2

	def format(self,add_comments=False):
		p = self.parent
		fh = (
			self.file_header_mn.format(p.pw_fmt.upper())
				if p.gen_passwds and p.pw_fmt in ('bip39','xmrseed') else
			self.file_header ).strip()
		from .globalvars import g
		out = [fh.format(pnm=g.proj_name,n=TwComment.max_screen_width) + '\n']

		if p.chksum:
			out.append(f'# {capfirst(p.desc)} data checksum for {p.id_str}: {p.chksum}')
			out.append('# Record this value to a secure location.\n')

		lbl = self.make_label()
		dmsg_sc('lbl',lbl[9:])
		out.append(f'{lbl} {{')

		fs = '  {:<%s}  {:<34}{}' % len(str(p.data[-1].idx))
		for e in p.data:
			c = ' ' + e.comment if add_comments and e.comment else ''
			if type(p) == KeyList:
				out.append(fs.format( e.idx, f'{p.al_id.mmtype.wif_label}: {e.sec.wif}', c ))
			elif type(p).__name__ == 'PasswordList':
				out.append(fs.format(e.idx,e.passwd,c))
			else: # First line with idx
				out.append(fs.format(e.idx,e.addr,c))
				if p.has_keys:
					from .opts import opt
					if opt.b16:
						out.append(fs.format( '', f'orig_hex: {e.sec.orig_bytes.hex()}', c ))
					out.append(fs.format( '', f'{p.al_id.mmtype.wif_label}: {e.sec.wif}', c ))
					for k in ('viewkey','wallet_passwd'):
						v = getattr(e,k)
						if v: out.append(fs.format( '', f'{k}: {v}', c ))

		out.append('}')
		self.fmt_data = '\n'.join([l.rstrip() for l in out]) + '\n'

	def get_line(self,lines):
		ret = lines.pop(0).split(None,2)
		self.line_ctr += 1
		if ret[0] == 'orig_hex:': # hacky
			ret = lines.pop(0).split(None,2)
			self.line_ctr += 1
		return ret if len(ret) == 3 else ret + ['']

	def parse_file_body(self,lines):

		p = self.parent
		ret = AddrListData()
		le = p.entry_type
		iifs = "{!r}: invalid identifier [expected '{}:']"

		while lines:
			idx,addr,comment = self.get_line(lines)

			assert is_addr_idx(idx), f'invalid address index {idx!r}'
			p.check_format(addr)

			a = le(**{ 'proto': p.proto, 'idx':int(idx), p.main_attr:addr, 'comment':comment })

			if p.has_keys: # order: wif,(orig_hex),viewkey,wallet_passwd
				d = self.get_line(lines)
				assert d[0] == p.al_id.mmtype.wif_label+':', iifs.format(d[0],p.al_id.mmtype.wif_label)
				a.sec = PrivKey(proto=p.proto,wif=d[1])
				for k,dtype,add_proto in (
					('viewkey',ViewKey,True),
					('wallet_passwd',WalletPassword,False) ):
					if k in p.al_id.mmtype.extra_attrs:
						d = self.get_line(lines)
						assert d[0] == k+':', iifs.format(d[0],k)
						setattr(a,k,dtype( *((p.proto,d[1]) if add_proto else (d[1],)) ) )

			ret.append(a)

		if p.has_keys and p.ka_validity_chk != False:

			def verify_keys():
				from .addrgen import KeyGenerator,AddrGenerator
				kg = KeyGenerator(p.proto,p.al_id.mmtype.pubkey_type)
				ag = AddrGenerator(p.proto,p.al_id.mmtype)
				llen = len(ret)
				for n,e in enumerate(ret):
					qmsg_r(f'\rVerifying keys {n+1}/{llen}')
					assert e.addr == ag.to_addr(kg.gen_data(e.sec)),(
						f'Key doesn’t match address!\n  {e.sec.wif}\n  {e.addr}')
				qmsg(' - done')

			from .opts import opt
			if opt.yes or p.ka_validity_chk == True:
				verify_keys()
			else:
				from .ui import keypress_confirm
				if keypress_confirm('Check key-to-address validity?'):
					verify_keys()

		return ret

	def parse_file(self,fn,buf=[],exit_on_error=True):

		def parse_addrfile_label(lbl):
			"""
			label examples:
			- Bitcoin legacy mainnet:   no label
			- Bitcoin legacy testnet:   'LEGACY:TESTNET'
			- Bitcoin Segwit:           'SEGWIT'
			- Bitcoin Segwit testnet:   'SEGWIT:TESTNET'
			- Bitcoin Bech32 regtest:   'BECH32:REGTEST'
			- Litecoin legacy mainnet:  'LTC'
			- Litecoin Bech32 mainnet:  'LTC:BECH32'
			- Litecoin legacy testnet:  'LTC:LEGACY:TESTNET'
			- Ethereum mainnet:         'ETH'
			- Ethereum Classic mainnet: 'ETC'
			- Ethereum regtest:         'ETH:REGTEST'
			"""
			lbl = lbl.lower()

			# remove the network component:
			if lbl.endswith(':testnet'):
				network = 'testnet'
				lbl = lbl[:-8]
			elif lbl.endswith(':regtest'):
				network = 'regtest'
				lbl = lbl[:-8]
			else:
				network = 'mainnet'

			from .proto.btc.params import mainnet
			if lbl in [MMGenAddrType(mainnet,key).name for key in mainnet.mmtypes]:
				coin,mmtype_key = ( 'BTC', lbl )
			elif ':' in lbl: # first component is coin, second is mmtype_key
				coin,mmtype_key = lbl.split(':')
			else:            # only component is coin
				coin,mmtype_key = ( lbl, None )

			proto = init_proto(coin=coin,network=network)

			if mmtype_key == None:
				mmtype_key = proto.mmtypes[0]

			return ( proto, proto.addr_type(mmtype_key) )

		p = self.parent
		from .fileutil import get_lines_from_file
		lines = get_lines_from_file(fn,p.desc+' data',trim_comments=True)

		try:
			assert len(lines) >= 3, f'Too few lines in address file ({len(lines)})'
			ls = lines[0].split()
			assert 1 < len(ls) < 5, f'Invalid first line for {p.gen_desc} file: {lines[0]!r}'
			assert ls[-1] == '{', f'{ls!r}: invalid first line'
			ls.pop()
			assert lines[-1] == '}', f'{lines[-1]!r}: invalid last line'
			sid = ls.pop(0)
			assert is_seed_id(sid), f'{sid!r}: invalid Seed ID'

			if type(p).__name__ == 'PasswordList' and len(ls) == 2:
				ss = ls.pop().split(':')
				assert len(ss) == 2, f'{ss!r}: invalid password length specifier (must contain colon)'
				p.set_pw_fmt(ss[0])
				p.set_pw_len(ss[1])
				p.pw_id_str = MMGenPWIDString(ls.pop())
				modname,funcname = p.pw_info[p.pw_fmt].chk_func.split('.')
				import importlib
				p.chk_func = getattr(importlib.import_module('mmgen.'+modname),funcname)
				proto = init_proto('btc') # FIXME: dummy protocol
				mmtype = MMGenPasswordType(proto,'P')
			elif len(ls) == 1:
				proto,mmtype = parse_addrfile_label(ls[0])
			elif len(ls) == 0:
				proto = init_proto('btc')
				mmtype = proto.addr_type('L')
			else:
				raise ValueError(f'{lines[0]}: Invalid first line for {p.gen_desc} file {fn!r}')

			if type(p).__name__ != 'PasswordList':
				if proto.base_coin != p.proto.base_coin or proto.network != p.proto.network:
					"""
					Having caller supply protocol and checking address file protocol against it here
					allows us to catch all mismatches in one place.  This behavior differs from that of
					transaction files, which determine the protocol independently, requiring the caller
					to check for protocol mismatches (e.g. mmgen.tx.completed.check_correct_chain())
					"""
					raise ValueError(
						f'{p.desc} file is '
						+ f'{proto.base_coin} {proto.network} but protocol is '
						+ f'{p.proto.base_coin} {p.proto.network}' )

			p.base_coin = proto.base_coin
			p.network = proto.network
			p.al_id = AddrListID(SeedID(sid=sid),mmtype)

			data = self.parse_file_body(lines[1:-1])
			assert isinstance(data,list),'Invalid file body data'
		except Exception as e:
			m = 'Invalid data in {} list file {!r}{} ({!s})'.format(
				p.desc,
				self.infile,
				(f', content line {self.line_ctr}' if self.line_ctr else ''),
				e )
			if exit_on_error:
				die(3,m)
			else:
				msg(m)
				return False

		return data

class KeyAddrFile(AddrFile):
	desc = 'secret keys'
	ext  = 'akeys'

class KeyFile(KeyAddrFile):
	ext         = 'keys'
	file_header = """
# {pnm} key file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
"""

class PasswordFile(AddrFile):
	desc        = 'passwords'
	ext         = 'pws'
	file_header = """
# {pnm} password file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
# A text label of {n} screen cells or less may be added to the right of each
# password.  The label may contain any printable ASCII symbol.
#
"""
	file_header_mn = """
# {{pnm}} {} password file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {{pnm}}.
#
"""

	def get_line(self,lines):

		self.line_ctr += 1
		p = self.parent

		if p.pw_fmt in ('bip39','xmrseed'):
			ret = lines.pop(0).split(None,p.pw_len+1)
			if len(ret) > p.pw_len+1:
				m1 = f'extraneous text {ret[p.pw_len+1]!r} found after password'
				m2 = '[bare comments not allowed in BIP39 password files]'
				m = m1+' '+m2
			elif len(ret) < p.pw_len+1:
				m = f'invalid password length {len(ret)-1}'
			else:
				return (ret[0],' '.join(ret[1:p.pw_len+1]),'')
			raise ValueError(m)
		else:
			ret = lines.pop(0).split(None,2)
			return ret if len(ret) == 3 else ret + ['']

	def make_label(self):
		p = self.parent
		return f'{p.al_id.sid} {p.pw_id_str} {p.pw_fmt_disp}:{p.pw_len}'

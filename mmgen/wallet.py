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
wallet.py:  Wallet classes and methods for the MMGen suite
"""

import os

from .common import *
from .obj import *
from .crypto import *
from .baseconv import *
from .seed import Seed

def check_usr_seed_len(seed_len):
	if opt.seed_len and opt.seed_len != seed_len:
		die(1,f'ERROR: requested seed length ({opt.seed_len}) doesn’t match seed length of source ({seed_len})')

def _is_mnemonic(s,fmt):
	oq_save = bool(opt.quiet)
	opt.quiet = True
	try:
		Wallet(in_data=s,in_fmt=fmt)
		ret = True
	except:
		ret = False
	finally:
		opt.quiet = oq_save
	return ret

def is_bip39_mnemonic(s): return _is_mnemonic(s,fmt='bip39')
def is_mmgen_mnemonic(s): return _is_mnemonic(s,fmt='words')

class WalletMeta(type):
	wallet_classes = set() # one-instance class, so store data in class attr
	def __init__(cls,name,bases,namespace):
		cls.wallet_classes.add(cls)
		cls.wallet_classes -= set(bases)

class Wallet(MMGenObject,metaclass=WalletMeta):

	desc = g.proj_name + ' seed source'
	file_mode = 'text'
	stdin_ok = False
	ask_tty = True
	no_tty  = False
	op = None
	_msg = {}

	class WalletData(MMGenObject): pass

	def __new__(cls,
		fn            = None,
		ss            = None,
		seed_bin      = None,
		seed          = None,
		passchg       = False,
		in_data       = None,
		ignore_in_fmt = False,
		in_fmt        = None ):

		in_fmt = in_fmt or opt.in_fmt

		if hasattr(opt,'out_fmt') and opt.out_fmt:
			out_cls = cls.fmt_code_to_type(opt.out_fmt)
			if not out_cls:
				die(1,f'{opt.out_fmt!r}: unrecognized output format')
		else:
			out_cls = None

		def die_on_opt_mismatch(opt,sstype):
			compare_or_die(
				cls.fmt_code_to_type(opt).__name__, 'input format requested on command line',
				sstype.__name__, 'input file format' )

		if seed or seed_bin:
			me = super(cls,cls).__new__(out_cls or MMGenWallet) # default to MMGenWallet
			me.seed = seed or Seed(seed_bin=seed_bin)
			me.op = 'new'
		elif ss:
			me = super(cls,cls).__new__((ss.__class__ if passchg else out_cls) or MMGenWallet)
			me.seed = ss.seed
			me.ss_in = ss
			me.op = ('conv','pwchg_new')[bool(passchg)]
		elif fn or opt.hidden_incog_input_params:
			from .filename import Filename
			if fn:
				f = Filename(fn)
			else:
				# permit comma in filename
				fn = ','.join(opt.hidden_incog_input_params.split(',')[:-1])
				f = Filename(fn,ftype=IncogWalletHidden)
			if in_fmt and not ignore_in_fmt:
				die_on_opt_mismatch(in_fmt,f.ftype)
			me = super(cls,cls).__new__(f.ftype)
			me.infile = f
			me.op = ('old','pwchg_old')[bool(passchg)]
		elif in_fmt:
			me = super(cls,cls).__new__(cls.fmt_code_to_type(in_fmt))
			me.op = ('old','pwchg_old')[bool(passchg)]
		else: # called with no arguments: initialize with random seed
			me = super(cls,cls).__new__(out_cls or MMGenWallet)
			me.seed = Seed(None)
			me.op = 'new'

		return me

	def __init__(self,
		fn            = None,
		ss            = None,
		seed_bin      = None,
		seed          = None,
		passchg       = False,
		in_data       = None,
		ignore_in_fmt = False,
		in_fmt        = None ):

		self.passwd_file = opt.passwd_file
		self.ssdata = self.WalletData()
		self.msg = {}
		self.in_data = in_data

		for c in reversed(self.__class__.__mro__):
			if hasattr(c,'_msg'):
				self.msg.update(c._msg)

		if hasattr(self,'seed'):
			self._encrypt()
			return
		elif hasattr(self,'infile') or self.in_data or not g.stdin_tty:
			self._deformat_once()
			self._decrypt_retry()
		else:
			if not self.stdin_ok:
				die(1,f'Reading from standard input not supported for {self.desc} format')
			self._deformat_retry()
			self._decrypt_retry()

		qmsg('Valid {} for Seed ID {}{}'.format(
			self.desc,
			self.seed.sid.hl(),
			(f', seed length {self.seed.bitlen}' if self.seed.bitlen != 256 else '')
		))

	def _get_data(self):
		if hasattr(self,'infile'):
			self.fmt_data = get_data_from_file(self.infile.name,self.desc,binary=self.file_mode=='binary')
		elif self.in_data:
			self.fmt_data = self.in_data
		else:
			self.fmt_data = self._get_data_from_user(self.desc)

	def _get_data_from_user(self,desc):
		return get_data_from_user(desc)

	def _deformat_once(self):
		self._get_data()
		if not self._deformat():
			die(2,'Invalid format for input data')

	def _deformat_retry(self):
		while True:
			self._get_data()
			if self._deformat():
				break
			msg('Trying again...')

	def _decrypt_retry(self):
		while True:
			if self._decrypt():
				break
			if self.passwd_file:
				die(2,'Passphrase from password file, so exiting')
			msg('Trying again...')

	@classmethod
	def get_extensions(cls):
		return [c.ext for c in cls.wallet_classes if hasattr(c,'ext')]

	@classmethod
	def fmt_code_to_type(cls,fmt_code):
		if fmt_code:
			for c in cls.wallet_classes:
				if fmt_code in getattr(c,'fmt_codes',[]):
					return c
		return None

	@classmethod
	def ext_to_type(cls,ext):
		if ext:
			for c in cls.wallet_classes:
				if ext == getattr(c,'ext',None):
					return c
		return None

	@classmethod
	def format_fmt_codes(cls):
		d = [(c.__name__,('.'+c.ext if c.ext else str(c.ext)),','.join(c.fmt_codes))
					for c in cls.wallet_classes
				if hasattr(c,'fmt_codes')]
		w = max(len(i[0]) for i in d)
		ret = [f'{a:<{w}}  {b:<9} {c}' for a,b,c in [
			('Format','FileExt','Valid codes'),
			('------','-------','-----------')
			] + sorted(d)]
		return '\n'.join(ret) + ('','-α')[g.debug_utf8] + '\n'

	def get_fmt_data(self):
		self._format()
		return self.fmt_data

	def write_to_file(self,outdir='',desc=''):
		self._format()
		kwargs = {
			'desc':     desc or self.desc,
			'ask_tty':  self.ask_tty,
			'no_tty':   self.no_tty,
			'binary':   self.file_mode == 'binary'
		}
		# write_data_to_file(): outfile with absolute path overrides opt.outdir
		if outdir:
			of = os.path.abspath(os.path.join(outdir,self._filename()))
		write_data_to_file(of if outdir else self._filename(),self.fmt_data,**kwargs)

class WalletUnenc(Wallet):

	def _decrypt_retry(self): pass
	def _encrypt(self): pass

	def _filename(self):
		s = self.seed
		return '{}[{}]{x}.{}'.format(
			s.fn_stem,
			s.bitlen,
			self.ext,
			x='-α' if g.debug_utf8 else '')

	def _choose_seedlen(self,desc,ok_lens,subtype):

		from .term import get_char
		def choose_len():
			prompt = self.choose_seedlen_prompt
			while True:
				r = get_char('\r'+prompt)
				if is_int(r) and 1 <= int(r) <= len(ok_lens):
					break
			msg_r(('\r','\n')[g.test_suite] + ' '*len(prompt) + '\r')
			return ok_lens[int(r)-1]

		msg('{} {}'.format(
			blue(f'{capfirst(desc)} type:'),
			yellow(subtype)
		))

		while True:
			usr_len = choose_len()
			prompt = self.choose_seedlen_confirm.format(usr_len)
			if keypress_confirm(prompt,default_yes=True,no_nl=not g.test_suite):
				return usr_len

class WalletEnc(Wallet):

	_msg = {
		'choose_passphrase': """
			You must choose a passphrase to encrypt your new {} with.
			A key will be generated from your passphrase using a hash preset of '{}'.
			Please note that no strength checking of passphrases is performed.
			For an empty passphrase, just hit ENTER twice.
		"""
	}

	def _get_hash_preset_from_user(self,hp,add_desc=''):
		prompt = 'Enter {}hash preset for {}{}{},\nor hit ENTER to {} value ({!r}): '.format(
			('old ' if self.op=='pwchg_old' else 'new ' if self.op=='pwchg_new' else ''),
			('','new ')[self.op=='new'],
			self.desc,
			('',' '+add_desc)[bool(add_desc)],
			('accept the default','reuse the old')[self.op=='pwchg_new'],
			hp )
		while True:
			ret = line_input(prompt)
			if ret:
				if ret in g.hash_presets:
					return ret
				else:
					msg('Invalid input.  Valid choices are {}'.format(', '.join(g.hash_presets)))
			else:
				return hp

	def _get_hash_preset(self,add_desc=''):
		if hasattr(self,'ss_in') and hasattr(self.ss_in.ssdata,'hash_preset'):
			old_hp = self.ss_in.ssdata.hash_preset
			if opt.keep_hash_preset:
				hp = old_hp
				qmsg(f'Reusing hash preset {hp!r} at user request')
			elif opt.hash_preset:
				hp = opt.hash_preset
				qmsg(f'Using hash preset {hp!r} requested on command line')
			else: # Prompt, using old value as default
				hp = self._get_hash_preset_from_user(old_hp,add_desc)
			if (not opt.keep_hash_preset) and self.op == 'pwchg_new':
				qmsg('Hash preset {}'.format( 'unchanged' if hp == old_hp else f'changed to {hp!r}' ))
		elif opt.hash_preset:
			hp = opt.hash_preset
			qmsg(f'Using hash preset {hp!r} requested on command line')
		else:
			hp = self._get_hash_preset_from_user(g.dfl_hash_preset,add_desc)
		self.ssdata.hash_preset = hp

	def _get_new_passphrase(self):
		desc = '{}passphrase for {}{}'.format(
				('','new ')[self.op=='pwchg_new'],
				('','new ')[self.op in ('new','conv')],
				self.desc
			)
		if self.passwd_file:
			pw = ' '.join(get_words_from_file(
				self.passwd_file,
				desc,
				quiet = pwfile_reuse_warning(self.passwd_file).warning_shown ))
		else:
			qmsg('\n'+fmt(self.msg['choose_passphrase'].format(self.desc,self.ssdata.hash_preset),indent='  '))
			if opt.echo_passphrase:
				pw = ' '.join(get_words_from_user(f'Enter {desc}: '))
			else:
				for i in range(g.passwd_max_tries):
					pw = ' '.join(get_words_from_user(f'Enter {desc}: '))
					pw_chk = ' '.join(get_words_from_user('Repeat passphrase: '))
					dmsg(f'Passphrases: [{pw}] [{pw_chk}]')
					if pw == pw_chk:
						vmsg('Passphrases match')
						break
					else:
						msg('Passphrases do not match.  Try again.')
				else:
					die(2,f'User failed to duplicate passphrase in {g.passwd_max_tries} attempts')

		if pw == '':
			qmsg('WARNING: Empty passphrase')
		self.ssdata.passwd = pw
		return pw

	def _get_passphrase(self,add_desc=''):
		desc = '{}passphrase for {}{}'.format(
			('','old ')[self.op=='pwchg_old'],
			self.desc,
			('',' '+add_desc)[bool(add_desc)]
		)
		if self.passwd_file:
			ret = ' '.join(get_words_from_file(
				self.passwd_file,
				desc,
				quiet = pwfile_reuse_warning(self.passwd_file).warning_shown ))
		else:
			ret = ' '.join(get_words_from_user(f'Enter {desc}: '))
		self.ssdata.passwd = ret

	def _get_first_pw_and_hp_and_encrypt_seed(self):
		d = self.ssdata
		self._get_hash_preset()

		if hasattr(self,'ss_in') and hasattr(self.ss_in.ssdata,'passwd'):
			old_pw = self.ss_in.ssdata.passwd
			if opt.keep_passphrase:
				d.passwd = old_pw
				qmsg('Reusing passphrase at user request')
			else:
				pw = self._get_new_passphrase()
				if self.op == 'pwchg_new':
					qmsg('Passphrase {}'.format( 'unchanged' if pw == old_pw else 'changed' ))
		else:
			self._get_new_passphrase()

		d.salt     = sha256(get_random(128)).digest()[:g.salt_len]
		key        = make_key(d.passwd, d.salt, d.hash_preset)
		d.key_id   = make_chksum_8(key)
		d.enc_seed = encrypt_seed(self.seed.data,key)

class Mnemonic(WalletUnenc):

	stdin_ok = True
	wclass = 'mnemonic'
	conv_cls = baseconv
	choose_seedlen_prompt = 'Choose a mnemonic length: 1) 12 words, 2) 18 words, 3) 24 words: '
	choose_seedlen_confirm = 'Mnemonic length of {} words chosen. OK?'

	@property
	def mn_lens(self):
		return sorted(self.conv_cls.seedlen_map_rev[self.wl_id])

	def _get_data_from_user(self,desc):

		if not g.stdin_tty:
			return get_data_from_user(desc)

		from .mn_entry import mn_entry # import here to catch cfg var errors
		mn_len = self._choose_seedlen(self.wclass,self.mn_lens,self.mn_type)
		return mn_entry(self.wl_id).get_mnemonic_from_user(mn_len)

	@staticmethod
	def _mn2hex_pad(mn): return len(mn) * 8 // 3

	@staticmethod
	def _hex2mn_pad(hexnum): return len(hexnum) * 3 // 8

	def _format(self):

		hexseed = self.seed.hexdata

		mn  = self.conv_cls.fromhex(hexseed,self.wl_id,self._hex2mn_pad(hexseed))
		ret = self.conv_cls.tohex(mn,self.wl_id,self._mn2hex_pad(mn))

		# Internal error, so just die on fail
		compare_or_die(ret,'recomputed seed',hexseed,'original',e='Internal error')

		self.ssdata.mnemonic = mn
		self.fmt_data = ' '.join(mn) + '\n'

	def _deformat(self):

		self.conv_cls.init_mn(self.wl_id)
		mn = self.fmt_data.split()

		if len(mn) not in self.mn_lens:
			msg('Invalid mnemonic ({} words).  Valid numbers of words: {}'.format(
				len(mn),
				', '.join(map(str,self.mn_lens)) ))
			return False

		for n,w in enumerate(mn,1):
			if w not in self.conv_cls.digits[self.wl_id]:
				msg(f'Invalid mnemonic: word #{n} is not in the {self.wl_id.upper()} wordlist')
				return False

		hexseed = self.conv_cls.tohex(mn,self.wl_id,self._mn2hex_pad(mn))
		ret     = self.conv_cls.fromhex(hexseed,self.wl_id,self._hex2mn_pad(hexseed))

		if len(hexseed) * 4 not in g.seed_lens:
			msg('Invalid mnemonic (produces too large a number)')
			return False

		# Internal error, so just die
		compare_or_die(' '.join(ret),'recomputed mnemonic',' '.join(mn),'original',e='Internal error')

		self.seed = Seed(bytes.fromhex(hexseed))
		self.ssdata.mnemonic = mn

		check_usr_seed_len(self.seed.bitlen)

		return True

class MMGenMnemonic(Mnemonic):

	fmt_codes = ('mmwords','words','mnemonic','mnem','mn','m')
	desc = 'MMGen native mnemonic data'
	mn_type = 'MMGen native'
	ext = 'mmwords'
	wl_id = 'mmgen'

class BIP39Mnemonic(Mnemonic):

	fmt_codes = ('bip39',)
	desc = 'BIP39 mnemonic data'
	mn_type = 'BIP39'
	ext = 'bip39'
	wl_id = 'bip39'

	def __init__(self,*args,**kwargs):
		from .bip39 import bip39
		self.conv_cls = bip39
		super().__init__(*args,**kwargs)

class MMGenSeedFile(WalletUnenc):

	stdin_ok = True
	fmt_codes = ('mmseed','seed','s')
	desc = 'seed data'
	ext = 'mmseed'

	def _format(self):
		b58seed = baseconv.frombytes(self.seed.data,'b58',pad='seed',tostr=True)
		self.ssdata.chksum = make_chksum_6(b58seed)
		self.ssdata.b58seed = b58seed
		self.fmt_data = '{} {}\n'.format(
			self.ssdata.chksum,
			split_into_cols(4,b58seed) )

	def _deformat(self):
		desc = self.desc
		ld = self.fmt_data.split()

		if not (7 <= len(ld) <= 12): # 6 <= padded b58 data (ld[1:]) <= 11
			msg(f'Invalid data length ({len(ld)}) in {desc}')
			return False

		a,b = ld[0],''.join(ld[1:])

		if not is_chksum_6(a):
			msg(f'{a!r}: invalid checksum format in {desc}')
			return False

		if not is_b58_str(b):
			msg(f'{b!r}: not a base 58 string, in {desc}')
			return False

		vmsg_r(f'Validating {desc} checksum...')

		if not compare_chksums(a,'file',make_chksum_6(b),'computed',verbose=True):
			return False

		ret = baseconv.tobytes(b,'b58',pad='seed')

		if ret == False:
			msg(f'Invalid base-58 encoded seed: {val}')
			return False

		self.seed = Seed(ret)
		self.ssdata.chksum = a
		self.ssdata.b58seed = b

		check_usr_seed_len(self.seed.bitlen)

		return True

class DieRollSeedFile(WalletUnenc):

	stdin_ok = True
	fmt_codes = ('b6d','die','dieroll')
	desc = 'base6d die roll seed data'
	ext = 'b6d'
	conv_cls = baseconv
	wclass = 'dieroll'
	wl_id = 'b6d'
	mn_type = 'base6d'
	choose_seedlen_prompt = 'Choose a seed length: 1) 128 bits, 2) 192 bits, 3) 256 bits: '
	choose_seedlen_confirm = 'Seed length of {} bits chosen. OK?'
	user_entropy_prompt = 'Would you like to provide some additional entropy from the keyboard?'
	interactive_input = False

	def _format(self):
		d = baseconv.frombytes(self.seed.data,'b6d',pad='seed',tostr=True) + '\n'
		self.fmt_data = block_format(d,gw=5,cols=5)

	def _deformat(self):

		d = remove_whitespace(self.fmt_data)

		rmap = self.conv_cls.seedlen_map_rev['b6d']
		if not len(d) in rmap:
			raise SeedLengthError('{!r}: invalid length for {} (must be one of {})'.format(
				len(d),
				self.desc,
				list(rmap) ))

		# truncate seed to correct length, discarding high bits
		seed_len = rmap[len(d)]
		seed_bytes = baseconv.tobytes(d,'b6d',pad='seed')[-seed_len:]

		if self.interactive_input and opt.usr_randchars:
			if keypress_confirm(self.user_entropy_prompt):
				seed_bytes = add_user_random(
					rand_bytes = seed_bytes,
					desc       = 'gathered from your die rolls' )
				self.desc += ' plus user-supplied entropy'

		self.seed = Seed(seed_bytes)
		self.ssdata.hexseed = seed_bytes.hex()

		check_usr_seed_len(self.seed.bitlen)
		return True

	def _get_data_from_user(self,desc):

		if not g.stdin_tty:
			return get_data_from_user(desc)

		seed_bitlens = [n*8 for n in sorted(self.conv_cls.seedlen_map['b6d'])]
		seed_bitlen = self._choose_seedlen(self.wclass,seed_bitlens,self.mn_type)
		nDierolls = self.conv_cls.seedlen_map['b6d'][seed_bitlen // 8]

		m = """
			For a {sb}-bit seed you must roll the die {nd} times.  After each die roll,
			enter the result on the keyboard as a digit.  If you make an invalid entry,
			you'll be prompted to re-enter it.
		"""
		msg('\n'+fmt(m.strip()).format(sb=seed_bitlen,nd=nDierolls)+'\n')

		b6d_digits = self.conv_cls.digits['b6d']

		cr = '\n' if g.test_suite else '\r'
		prompt_fs = f'\b\b\b   {cr}Enter die roll #{{}}: {CUR_SHOW}'
		clear_line = '' if g.test_suite else '\r' + ' ' * 25
		invalid_msg = CUR_HIDE + cr + 'Invalid entry' + ' ' * 11

		from .term import get_char
		def get_digit(n):
			p = prompt_fs
			sleep = g.short_disp_timeout
			while True:
				ch = get_char(p.format(n),num_chars=1,sleep=sleep)
				if ch in b6d_digits:
					msg_r(CUR_HIDE + ' OK')
					return ch
				else:
					msg_r(invalid_msg)
					sleep = g.err_disp_timeout
					p = clear_line + prompt_fs

		dierolls,n = [],1
		while len(dierolls) < nDierolls:
			dierolls.append(get_digit(n))
			n += 1

		msg('Die rolls successfully entered' + CUR_SHOW)
		self.interactive_input = True

		return ''.join(dierolls)

class PlainHexSeedFile(WalletUnenc):

	stdin_ok = True
	fmt_codes = ('hex','rawhex','plainhex')
	desc = 'plain hexadecimal seed data'
	ext = 'hex'

	def _format(self):
		self.fmt_data = self.seed.hexdata + '\n'

	def _deformat(self):
		desc = self.desc
		d = self.fmt_data.strip()

		if not is_hex_str_lc(d):
			msg(f'{d!r}: not a lowercase hexadecimal string, in {desc}')
			return False

		if not len(d)*4 in g.seed_lens:
			msg(f'Invalid data length ({len(d)}) in {desc}')
			return False

		self.seed = Seed(bytes.fromhex(d))
		self.ssdata.hexseed = d

		check_usr_seed_len(self.seed.bitlen)

		return True

class MMGenHexSeedFile(WalletUnenc):

	stdin_ok = True
	fmt_codes = ('seedhex','hexseed','mmhex')
	desc = 'hexadecimal seed data with checksum'
	ext = 'mmhex'

	def _format(self):
		h = self.seed.hexdata
		self.ssdata.chksum = make_chksum_6(h)
		self.ssdata.hexseed = h
		self.fmt_data = '{} {}\n'.format(
			self.ssdata.chksum,
			split_into_cols(4,h) )

	def _deformat(self):
		desc = self.desc
		d = self.fmt_data.split()
		try:
			d[1]
			chk,hstr = d[0],''.join(d[1:])
		except:
			msg(f'{self.fmt_data.strip()!r}: invalid {desc}')
			return False

		if not len(hstr)*4 in g.seed_lens:
			msg(f'Invalid data length ({len(hstr)}) in {desc}')
			return False

		if not is_chksum_6(chk):
			msg(f'{chk!r}: invalid checksum format in {desc}')
			return False

		if not is_hex_str(hstr):
			msg(f'{hstr!r}: not a hexadecimal string, in {desc}')
			return False

		vmsg_r(f'Validating {desc} checksum...')

		if not compare_chksums(chk,'file',make_chksum_6(hstr),'computed',verbose=True):
			return False

		self.seed = Seed(bytes.fromhex(hstr))
		self.ssdata.chksum = chk
		self.ssdata.hexseed = hstr

		check_usr_seed_len(self.seed.bitlen)

		return True

class MMGenWallet(WalletEnc):

	fmt_codes = ('wallet','w')
	desc = g.proj_name + ' wallet'
	ext = 'mmdat'

	def __init__(self,*args,**kwargs):
		if opt.label:
			self.label = MMGenWalletLabel(
				opt.label,
				msg = "Error in option '--label'" )
		else:
			self.label = None
		super().__init__(*args,**kwargs)

	# logic identical to _get_hash_preset_from_user()
	def _get_label_from_user(self,old_lbl=''):
		prompt = 'Enter a wallet label, or hit ENTER {}: '.format(
			'to reuse the label {}'.format(old_lbl.hl(encl="''")) if old_lbl else
			'for no label' )
		while True:
			ret = line_input(prompt)
			if ret:
				lbl = get_obj(MMGenWalletLabel,s=ret)
				if lbl:
					return lbl
				else:
					msg('Invalid label.  Trying again...')
			else:
				return old_lbl or MMGenWalletLabel('No Label')

	# logic identical to _get_hash_preset()
	def _get_label(self):
		if hasattr(self,'ss_in') and hasattr(self.ss_in.ssdata,'label'):
			old_lbl = self.ss_in.ssdata.label
			if opt.keep_label:
				lbl = old_lbl
				qmsg('Reusing label {} at user request'.format( lbl.hl(encl="''") ))
			elif self.label:
				lbl = self.label
				qmsg('Using label {} requested on command line'.format( lbl.hl(encl="''") ))
			else: # Prompt, using old value as default
				lbl = self._get_label_from_user(old_lbl)
			if (not opt.keep_label) and self.op == 'pwchg_new':
				qmsg('Label {}'.format( 'unchanged' if lbl == old_lbl else f'changed to {lbl!r}' ))
		elif self.label:
			lbl = self.label
			qmsg('Using label {} requested on command line'.format( lbl.hl(encl="''") ))
		else:
			lbl = self._get_label_from_user()
		self.ssdata.label = lbl

	def _encrypt(self):
		self._get_first_pw_and_hp_and_encrypt_seed()
		self._get_label()
		d = self.ssdata
		d.pw_status = ('NE','E')[len(d.passwd)==0]
		d.timestamp = make_timestamp()

	def _format(self):
		d = self.ssdata
		s = self.seed
		slt_fmt  = baseconv.frombytes(d.salt,'b58',pad='seed',tostr=True)
		es_fmt = baseconv.frombytes(d.enc_seed,'b58',pad='seed',tostr=True)
		lines = (
			d.label,
			'{} {} {} {} {}'.format( s.sid.lower(), d.key_id.lower(), s.bitlen, d.pw_status, d.timestamp ),
			'{}: {} {} {}'.format( d.hash_preset, *get_hash_params(d.hash_preset) ),
			'{} {}'.format( make_chksum_6(slt_fmt), split_into_cols(4,slt_fmt) ),
			'{} {}'.format( make_chksum_6(es_fmt),  split_into_cols(4,es_fmt) )
		)
		chksum = make_chksum_6(' '.join(lines).encode())
		self.fmt_data = '\n'.join((chksum,)+lines) + '\n'

	def _deformat(self):

		def check_master_chksum(lines,desc):

			if len(lines) != 6:
				msg(f'Invalid number of lines ({len(lines)}) in {desc} data')
				return False

			if not is_chksum_6(lines[0]):
				msg(f'Incorrect master checksum ({lines[0]}) in {desc} data')
				return False

			chk = make_chksum_6(' '.join(lines[1:]))
			if not compare_chksums(lines[0],'master',chk,'computed',
						hdr='For wallet master checksum',verbose=True):
				return False

			return True

		lines = self.fmt_data.splitlines()
		if not check_master_chksum(lines,self.desc):
			return False

		d = self.ssdata
		d.label = MMGenWalletLabel(lines[1])

		d1,d2,d3,d4,d5 = lines[2].split()
		d.seed_id = d1.upper()
		d.key_id  = d2.upper()
		check_usr_seed_len(int(d3))
		d.pw_status,d.timestamp = d4,d5

		hpdata = lines[3].split()

		d.hash_preset = hp = hpdata[0][:-1]  # a string!
		qmsg(f'Hash preset of wallet: {hp!r}')
		if opt.hash_preset and opt.hash_preset != hp:
			qmsg('Warning: ignoring user-requested hash preset {opt.hash_preset}')

		hash_params = tuple(map(int,hpdata[1:]))

		if hash_params != get_hash_params(d.hash_preset):
			msg(f'Hash parameters {" ".join(hash_params)!r} don’t match hash preset {d.hash_preset!r}')
			return False

		lmin,foo,lmax = sorted(baseconv.seedlen_map_rev['b58']) # 22,33,44
		for i,key in (4,'salt'),(5,'enc_seed'):
			l = lines[i].split(' ')
			chk = l.pop(0)
			b58_val = ''.join(l)

			if len(b58_val) < lmin or len(b58_val) > lmax:
				msg(f'Invalid format for {key} in {self.desc}: {l}')
				return False

			if not compare_chksums(chk,key,
					make_chksum_6(b58_val),'computed checksum',verbose=True):
				return False

			val = baseconv.tobytes(b58_val,'b58',pad='seed')
			if val == False:
				msg(f'Invalid base 58 number: {b58_val}')
				return False

			setattr(d,key,val)

		return True

	def _decrypt(self):
		d = self.ssdata
		# Needed for multiple transactions with {}-txsign
		self._get_passphrase(
			add_desc = os.path.basename(self.infile.name) if opt.quiet else '' )
		key = make_key(d.passwd, d.salt, d.hash_preset)
		ret = decrypt_seed(d.enc_seed, key, d.seed_id, d.key_id)
		if ret:
			self.seed = Seed(ret)
			return True
		else:
			return False

	def _filename(self):
		s = self.seed
		d = self.ssdata
		return '{}-{}[{},{}]{x}.{}'.format(
				s.fn_stem,
				d.key_id,
				s.bitlen,
				d.hash_preset,
				self.ext,
				x='-α' if g.debug_utf8 else '')

class Brainwallet(WalletEnc):

	stdin_ok = True
	fmt_codes = ('mmbrain','brainwallet','brain','bw','b')
	desc = 'brainwallet'
	ext = 'mmbrain'
	# brainwallet warning message? TODO

	def get_bw_params(self):
		# already checked
		a = opt.brain_params.split(',')
		return int(a[0]),a[1]

	def _deformat(self):
		self.brainpasswd = ' '.join(self.fmt_data.split())
		return True

	def _decrypt(self):
		d = self.ssdata
		if opt.brain_params:
			"""
			Don't set opt.seed_len!  When using multiple wallets, BW seed len might differ from others
			"""
			bw_seed_len,d.hash_preset = self.get_bw_params()
		else:
			if not opt.seed_len:
				qmsg(f'Using default seed length of {yellow(str(g.dfl_seed_len))} bits\n'
					+ 'If this is not what you want, use the --seed-len option' )
			self._get_hash_preset()
			bw_seed_len = opt.seed_len or g.dfl_seed_len
		qmsg_r('Hashing brainwallet data.  Please wait...')
		# Use buflen arg of scrypt.hash() to get seed of desired length
		seed = scrypt_hash_passphrase(
			self.brainpasswd.encode(),
			b'',
			d.hash_preset,
			buflen = bw_seed_len // 8 )
		qmsg('Done')
		self.seed = Seed(seed)
		msg(f'Seed ID: {self.seed.sid}')
		qmsg('Check this value against your records')
		return True

	def _format(self):
		raise NotImplementedError('Brainwallet not supported as an output format')

	def _encrypt(self):
		raise NotImplementedError('Brainwallet not supported as an output format')

class IncogWalletBase(WalletEnc):

	_msg = {
		'check_incog_id': """
  Check the generated Incog ID above against your records.  If it doesn't
  match, then your incognito data is incorrect or corrupted.
	""",
		'record_incog_id': """
  Make a record of the Incog ID but keep it secret.  You will use it to
  identify your incog wallet data in the future.
	""",
		'incorrect_incog_passphrase_try_again': """
Incorrect passphrase, hash preset, or maybe old-format incog wallet.
Try again? (Y)es, (n)o, (m)ore information:
""".strip(),
		'confirm_seed_id': """
If the Seed ID above is correct but you're seeing this message, then you need
to exit and re-run the program with the '--old-incog-fmt' option.
""".strip(),
		'dec_chk': " {} hash preset"
	}

	def _make_iv_chksum(self,s): return sha256(s).hexdigest()[:8].upper()

	def _get_incog_data_len(self,seed_len):
		e = (g.hincog_chk_len,0)[bool(opt.old_incog_fmt)]
		return g.aesctr_iv_len + g.salt_len + e + seed_len//8

	def _incog_data_size_chk(self):
		# valid sizes: 56, 64, 72
		dlen = len(self.fmt_data)
		seed_len = opt.seed_len or g.dfl_seed_len
		valid_dlen = self._get_incog_data_len(seed_len)
		if dlen == valid_dlen:
			return True
		else:
			if opt.old_incog_fmt:
				msg('WARNING: old-style incognito format requested.  Are you sure this is correct?')
			msg(f'Invalid incognito data size ({dlen} bytes) for this seed length ({seed_len} bits)')
			msg(f'Valid data size for this seed length: {valid_dlen} bytes')
			for sl in g.seed_lens:
				if dlen == self._get_incog_data_len(sl):
					die(1,f'Valid seed length for this data size: {sl} bits')
			msg(f'This data size ({dlen} bytes) is invalid for all available seed lengths')
			return False

	def _encrypt (self):
		self._get_first_pw_and_hp_and_encrypt_seed()
		if opt.old_incog_fmt:
			die(1,'Writing old-format incog wallets is unsupported')
		d = self.ssdata
		# IV is used BOTH to initialize counter and to salt password!
		d.iv = get_random(g.aesctr_iv_len)
		d.iv_id = self._make_iv_chksum(d.iv)
		msg(f'New Incog Wallet ID: {d.iv_id}')
		qmsg('Make a record of this value')
		vmsg(self.msg['record_incog_id'])

		d.salt = get_random(g.salt_len)
		key = make_key(d.passwd, d.salt, d.hash_preset, 'incog wallet key')
		chk = sha256(self.seed.data).digest()[:8]
		d.enc_seed = encrypt_data(chk+self.seed.data, key, g.aesctr_dfl_iv, 'seed')

		d.wrapper_key = make_key(d.passwd, d.iv, d.hash_preset, 'incog wrapper key')
		d.key_id = make_chksum_8(d.wrapper_key)
		vmsg(f'Key ID: {d.key_id}')
		d.target_data_len = self._get_incog_data_len(self.seed.bitlen)

	def _format(self):
		d = self.ssdata
		self.fmt_data = d.iv + encrypt_data(d.salt+d.enc_seed, d.wrapper_key, d.iv, self.desc)

	def _filename(self):
		s = self.seed
		d = self.ssdata
		return '{}-{}-{}[{},{}]{x}.{}'.format(
				s.fn_stem,
				d.key_id,
				d.iv_id,
				s.bitlen,
				d.hash_preset,
				self.ext,
				x='-α' if g.debug_utf8 else '')

	def _deformat(self):

		if not self._incog_data_size_chk():
			return False

		d = self.ssdata
		d.iv             = self.fmt_data[0:g.aesctr_iv_len]
		d.incog_id       = self._make_iv_chksum(d.iv)
		d.enc_incog_data = self.fmt_data[g.aesctr_iv_len:]
		msg(f'Incog Wallet ID: {d.incog_id}')
		qmsg('Check this value against your records')
		vmsg(self.msg['check_incog_id'])

		return True

	def _verify_seed_newfmt(self,data):
		chk,seed = data[:8],data[8:]
		if sha256(seed).digest()[:8] == chk:
			qmsg('Passphrase{} are correct'.format( self.msg['dec_chk'].format('and') ))
			return seed
		else:
			msg('Incorrect passphrase{}'.format( self.msg['dec_chk'].format('or') ))
			return False

	def _verify_seed_oldfmt(self,seed):
		m = f'Seed ID: {make_chksum_8(seed)}.  Is the Seed ID correct?'
		if keypress_confirm(m, True):
			return seed
		else:
			return False

	def _decrypt(self):
		d = self.ssdata
		self._get_hash_preset(add_desc=d.incog_id)
		self._get_passphrase(add_desc=d.incog_id)

		# IV is used BOTH to initialize counter and to salt password!
		key = make_key(d.passwd, d.iv, d.hash_preset, 'wrapper key')
		dd = decrypt_data(d.enc_incog_data, key, d.iv, 'incog data')

		d.salt     = dd[0:g.salt_len]
		d.enc_seed = dd[g.salt_len:]

		key = make_key(d.passwd, d.salt, d.hash_preset, 'main key')
		qmsg(f'Key ID: {make_chksum_8(key)}')

		verify_seed = getattr(self,'_verify_seed_'+
						('newfmt','oldfmt')[bool(opt.old_incog_fmt)])

		seed = verify_seed(decrypt_seed(d.enc_seed, key, '', ''))

		if seed:
			self.seed = Seed(seed)
			msg(f'Seed ID: {self.seed.sid}')
			return True
		else:
			return False

class IncogWallet(IncogWalletBase):

	desc = 'incognito data'
	fmt_codes = ('mmincog','incog','icg','i')
	ext = 'mmincog'
	file_mode = 'binary'
	no_tty = True

class IncogWalletHex(IncogWalletBase):

	desc = 'hex incognito data'
	fmt_codes = ('mmincox','incox','incog_hex','xincog','ix','xi')
	ext = 'mmincox'
	file_mode = 'text'
	no_tty = False

	def _deformat(self):
		ret = decode_pretty_hexdump(self.fmt_data)
		if ret:
			self.fmt_data = ret
			return super()._deformat()
		else:
			return False

	def _format(self):
		super()._format()
		self.fmt_data = pretty_hexdump(self.fmt_data)

class IncogWalletHidden(IncogWalletBase):

	desc = 'hidden incognito data'
	fmt_codes = ('incog_hidden','hincog','ih','hi')
	ext = None
	file_mode = 'binary'
	no_tty = True

	_msg = {
		'choose_file_size': """
You must choose a size for your new hidden incog data.  The minimum size is
{} bytes, which puts the incog data right at the end of the file. Since you
probably want to hide your data somewhere in the middle of the file where it's
harder to find, you're advised to choose a much larger file size than this.
	""".strip(),
		'check_incog_id': """
  Check generated Incog ID above against your records.  If it doesn't
  match, then your incognito data is incorrect or corrupted, or you
  may have specified an incorrect offset.
	""",
		'record_incog_id': """
  Make a record of the Incog ID but keep it secret.  You will used it to
  identify the incog wallet data in the future and to locate the offset
  where the data is hidden in the event you forget it.
	""",
		'dec_chk': ', hash preset, offset {} seed length'
	}

	def _get_hincog_params(self,wtype):
		a = getattr(opt,'hidden_incog_'+ wtype +'_params').split(',')
		return ','.join(a[:-1]),int(a[-1]) # permit comma in filename

	def _check_valid_offset(self,fn,action):
		d = self.ssdata
		m = ('Input','Destination')[action=='write']
		if fn.size < d.hincog_offset + d.target_data_len:
			die(1,'{} file {!r} has length {}, too short to {} {} bytes of data at offset {}'.format(
				m,
				fn.name,
				fn.size,
				action,
				d.target_data_len,
				d.hincog_offset ))

	def _get_data(self):
		d = self.ssdata
		d.hincog_offset = self._get_hincog_params('input')[1]

		qmsg(f'Getting hidden incog data from file {self.infile.name!r}')

		# Already sanity-checked:
		d.target_data_len = self._get_incog_data_len(opt.seed_len or g.dfl_seed_len)
		self._check_valid_offset(self.infile,'read')

		flgs = os.O_RDONLY|os.O_BINARY if g.platform == 'win' else os.O_RDONLY
		fh = os.open(self.infile.name,flgs)
		os.lseek(fh,int(d.hincog_offset),os.SEEK_SET)
		self.fmt_data = os.read(fh,d.target_data_len)
		os.close(fh)
		qmsg(f'Data read from file {self.infile.name!r} at offset {d.hincog_offset}')

	# overrides method in Wallet
	def write_to_file(self):
		d = self.ssdata
		self._format()
		compare_or_die(d.target_data_len, 'target data length',
				len(self.fmt_data),'length of formatted ' + self.desc)

		k = ('output','input')[self.op=='pwchg_new']
		fn,d.hincog_offset = self._get_hincog_params(k)

		if opt.outdir and not os.path.dirname(fn):
			fn = os.path.join(opt.outdir,fn)

		check_offset = True
		try:
			os.stat(fn)
		except:
			if keypress_confirm(
					f'Requested file {fn!r} does not exist.  Create?',
					default_yes = True ):
				min_fsize = d.target_data_len + d.hincog_offset
				msg(self.msg['choose_file_size'].format(min_fsize))
				while True:
					fsize = parse_bytespec(line_input('Enter file size: '))
					if fsize >= min_fsize:
						break
					msg(f'File size must be an integer no less than {min_fsize}')

				from .tool import MMGenToolCmdFileUtil
				MMGenToolCmdFileUtil().rand2file(fn,str(fsize))
				check_offset = False
			else:
				die(1,'Exiting at user request')

		from .filename import Filename
		f = Filename(fn,ftype=type(self),write=True)

		dmsg('{} data len {}, offset {}'.format(
			capfirst(self.desc),
			d.target_data_len,
			d.hincog_offset ))

		if check_offset:
			self._check_valid_offset(f,'write')
			if not opt.quiet:
				confirm_or_raise( '', f'alter file {f.name!r}' )

		flgs = os.O_RDWR|os.O_BINARY if g.platform == 'win' else os.O_RDWR
		fh = os.open(f.name,flgs)
		os.lseek(fh, int(d.hincog_offset), os.SEEK_SET)
		os.write(fh, self.fmt_data)
		os.close(fh)
		msg('{} written to file {!r} at offset {}'.format(
			capfirst(self.desc),
			f.name,
			d.hincog_offset ))

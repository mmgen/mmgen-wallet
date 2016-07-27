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
seed.py:  Seed-related classes and methods for the MMGen suite
"""

import os
from binascii import hexlify,unhexlify

from mmgen.common import *
from mmgen.bitcoin import b58encode_pad,b58decode_pad,b58_lens
from mmgen.obj import *
from mmgen.filename import *
from mmgen.crypto import *

pnm = g.proj_name

def check_usr_seed_len(seed_len):
	if opt.seed_len != seed_len and 'seed_len' in opt.set_by_user:
		m = 'ERROR: requested seed length (%s) ' + \
			"doesn't match seed length of source (%s)"
		die(1, m % (opt.seed_len,seed_len))

class Seed(MMGenObject):
	def __init__(self,seed_bin=None):
		if not seed_bin:
			# Truncate random data for smaller seed lengths
			seed_bin = sha256(get_random(1033)).digest()[:opt.seed_len/8]
		elif len(seed_bin)*8 not in g.seed_lens:
			die(3,'%s: invalid seed length' % len(seed_bin))

		self.data      = seed_bin
		self.hexdata   = hexlify(seed_bin)
		self.sid       = SeedID(seed=self)
		self.length    = len(seed_bin) * 8

	def get_data(self):
		return self.data


class SeedSource(MMGenObject):

	desc = g.proj_name + ' seed source'
	file_mode = 'text'
	stdin_ok = False
	ask_tty = True
	no_tty  = False
	op = None
	_msg = {}

	class SeedSourceData(MMGenObject): pass

	def __new__(cls,fn=None,ss=None,seed=None,ignore_in_fmt=False,passchg=False):

		def die_on_opt_mismatch(opt,sstype):
			opt_sstype = cls.fmt_code_to_type(opt)
			compare_or_die(
				opt_sstype.__name__, 'input format requested on command line',
				sstype.__name__,     'input file format'
			)

		if ss:
			sstype = ss.__class__ if passchg else cls.fmt_code_to_type(opt.out_fmt)
			me = super(cls,cls).__new__(sstype or Wallet) # default: Wallet
			me.seed = ss.seed
			me.ss_in = ss
			me.op = ('conv','pwchg_new')[bool(passchg)]
		elif fn or opt.hidden_incog_input_params:
			if fn:
				f = Filename(fn)
			else:
				fn = opt.hidden_incog_input_params.split(',')[0]
				f = Filename(fn,ftype=IncogWalletHidden)
			if opt.in_fmt and not ignore_in_fmt:
				die_on_opt_mismatch(opt.in_fmt,f.ftype)
			me = super(cls,cls).__new__(f.ftype)
			me.infile = f
			me.op = ('old','pwchg_old')[bool(passchg)]
		elif opt.in_fmt:  # Input format
			sstype = cls.fmt_code_to_type(opt.in_fmt)
			me = super(cls,cls).__new__(sstype)
			me.op = ('old','pwchg_old')[bool(passchg)]
		else: # Called with no inputs - initialize with random seed
			sstype = cls.fmt_code_to_type(opt.out_fmt)
			me = super(cls,cls).__new__(sstype or Wallet) # default: Wallet
			me.seed = Seed(seed_bin=seed or None)
			me.op = 'new'
#			die(1,me.seed.sid.hl()) # DEBUG

		return me

	def __init__(self,fn=None,ss=None,seed=None,ignore_in_fmt=False,passchg=False):

		self.ssdata = self.SeedSourceData()
		self.msg = {}

		for c in reversed(self.__class__.__mro__):
			if hasattr(c,'_msg'):
				self.msg.update(c._msg)

		if hasattr(self,'seed'):
			g.use_urandchars = True
			self._encrypt()
			return
		elif hasattr(self,'infile'):
			self._deformat_once()
			self._decrypt_retry()
		else:
			if not self.stdin_ok:
				die(1,'Reading from standard input not supported for %s format'
						% self.desc)
			self._deformat_retry()
			self._decrypt_retry()

		m = ('',', seed length %s' % self.seed.length)[self.seed.length!=256]
		qmsg('Valid %s for Seed ID %s%s' % (self.desc,self.seed.sid.hl(),m))

	def _get_data(self):
		if hasattr(self,'infile'):
			self.fmt_data = get_data_from_file(self.infile.name,self.desc,
								binary=self.file_mode=='binary')
		else:
			self.fmt_data = get_data_from_user(self.desc)

	def _deformat_once(self):
		self._get_data()
		if not self._deformat():
			die(2,'Invalid format for input data')

	def _deformat_retry(self):
		while True:
			self._get_data()
			if self._deformat(): break
			msg('Trying again...')

	def _decrypt_retry(self):
		while True:
			if self._decrypt(): break
			if opt.passwd_file:
				die(2,'Passphrase from password file, so exiting')
			msg('Trying again...')

	@classmethod
	def get_subclasses(cls):
		if not hasattr(cls,'subclasses'):
			gl = globals()
			setattr(cls,'subclasses',
				[gl[k] for k in gl if type(gl[k]) == type and issubclass(gl[k],cls)])
		return cls.subclasses

	@classmethod
	def get_subclasses_str(cls):
		def GetSubclassesTree(cls):
			return ''.join([c.__name__ +' '+ GetSubclassesTree(c) for c in cls.__subclasses__()])
		return GetSubclassesTree(cls)

	@classmethod
	def get_extensions(cls):
		return [s.ext for s in cls.get_subclasses() if hasattr(s,'ext')]

	@classmethod
	def fmt_code_to_type(cls,fmt_code):
		if not fmt_code: return None
		for c in cls.get_subclasses():
			if hasattr(c,'fmt_codes') and fmt_code in c.fmt_codes:
				return c
		return None

	@classmethod
	def ext_to_type(cls,ext):
		if not ext: return None
		for c in cls.get_subclasses():
			if hasattr(c,'ext') and ext == c.ext:
				return c
		return None

	@classmethod
	def format_fmt_codes(cls):
		d = [(c.__name__,('.'+c.ext if c.ext else c.ext),','.join(c.fmt_codes))
					for c in cls.get_subclasses()
				if hasattr(c,'fmt_codes')]
		w = max([len(a) for a,b,c in d])
		ret = ['{:<{w}}  {:<9} {}'.format(a,b,c,w=w) for a,b,c in [
			('Format','FileExt','Valid codes'),
			('------','-------','-----------')
			] + sorted(d)]
		return '\n'.join(ret) + '\n'

	def get_fmt_data(self):
		self._format()
		return self.fmt_data

	def write_to_file(self):
		self._format()
		kwargs = {
			'desc':     self.desc,
			'ask_tty':  self.ask_tty,
			'no_tty':   self.no_tty,
			'binary':   self.file_mode == 'binary'
		}
		write_data_to_file(self._filename(),self.fmt_data,**kwargs)


class SeedSourceUnenc(SeedSource):

	def _decrypt_retry(self): pass
	def _encrypt(self): pass


class SeedSourceEnc(SeedSource):

	_msg = {
		'choose_passphrase': """
You must choose a passphrase to encrypt your new %s with.
A key will be generated from your passphrase using a hash preset of '%s'.
Please note that no strength checking of passphrases is performed.  For
an empty passphrase, just hit ENTER twice.
	""".strip()
	}

	def _get_hash_preset_from_user(self,hp,desc_suf=''):
# 					hp=a,
		n = ('','old ')[self.op=='pwchg_old']
		m,n = (('to accept the default',n),('to reuse the old','new '))[
						int(self.op=='pwchg_new')]
		fs = "Enter {}hash preset for {}{}{},\n or hit ENTER {} value ('{}'): "
		p = fs.format(
			n,
			('','new ')[self.op=='new'],
			self.desc,
			('',' '+desc_suf)[bool(desc_suf)],
			m,
			hp
		)
		while True:
			ret = my_raw_input(p)
			if ret:
				if ret in g.hash_presets.keys():
					self.ssdata.hash_preset = ret
					return ret
				else:
					msg('Invalid input.  Valid choices are %s' %
							', '.join(sorted(g.hash_presets.keys())))
			else:
				self.ssdata.hash_preset = hp
				return hp

	def _get_hash_preset(self,desc_suf=''):
		if hasattr(self,'ss_in') and hasattr(self.ss_in.ssdata,'hash_preset'):
			old_hp = self.ss_in.ssdata.hash_preset
			if opt.keep_hash_preset:
				qmsg("Reusing hash preset '%s' at user request" % old_hp)
				self.ssdata.hash_preset = old_hp
			elif 'hash_preset' in opt.set_by_user:
				hp = self.ssdata.hash_preset = opt.hash_preset
				qmsg("Using hash preset '%s' requested on command line"
						% opt.hash_preset)
			else: # Prompt, using old value as default
				hp = self._get_hash_preset_from_user(old_hp,desc_suf)

			if (not opt.keep_hash_preset) and self.op == 'pwchg_new':
				m = ("changed to '%s'" % hp,'unchanged')[hp==old_hp]
				qmsg('Hash preset %s' % m)
		elif 'hash_preset' in opt.set_by_user:
			self.ssdata.hash_preset = opt.hash_preset
			qmsg("Using hash preset '%s' requested on command line"%opt.hash_preset)
		else:
			self._get_hash_preset_from_user(opt.hash_preset,desc_suf)

	def _get_new_passphrase(self):
		desc = '{}passphrase for {}{}'.format(
				('','new ')[self.op=='pwchg_new'],
				('','new ')[self.op in ('new','conv')],
				self.desc
			)
		if opt.passwd_file:
			w = pwfile_reuse_warning()
			pw = ' '.join(get_words_from_file(opt.passwd_file,desc,silent=w))
		elif opt.echo_passphrase:
			pw = ' '.join(get_words_from_user('Enter %s: ' % desc))
		else:
			for i in range(g.passwd_max_tries):
				pw = ' '.join(get_words_from_user('Enter %s: ' % desc))
				pw2 = ' '.join(get_words_from_user('Repeat passphrase: '))
				dmsg('Passphrases: [%s] [%s]' % (pw,pw2))
				if pw == pw2:
					vmsg('Passphrases match'); break
				else: msg('Passphrases do not match.  Try again.')
			else:
				die(2,'User failed to duplicate passphrase in %s attempts' %
						g.passwd_max_tries)

		if pw == '': qmsg('WARNING: Empty passphrase')
		self.ssdata.passwd = pw
		return pw

	def _get_passphrase(self,desc_suf=''):
		desc ='{}passphrase for {}{}'.format(
			('','old ')[self.op=='pwchg_old'],
			self.desc,
			('',' '+desc_suf)[bool(desc_suf)]
		)
		if opt.passwd_file:
			w = pwfile_reuse_warning()
			ret = ' '.join(get_words_from_file(opt.passwd_file,desc,silent=w))
		else:
			ret = ' '.join(get_words_from_user('Enter %s: ' % desc))
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
					m = ('changed','unchanged')[pw==old_pw]
					qmsg('Passphrase %s' % m)
		else:
			qmsg(self.msg['choose_passphrase'] % (self.desc,d.hash_preset))
			self._get_new_passphrase()

		d.salt     = sha256(get_random(128)).digest()[:g.salt_len]
		key        = make_key(d.passwd, d.salt, d.hash_preset)
		d.key_id   = make_chksum_8(key)
		d.enc_seed = encrypt_seed(self.seed.data,key)


class Mnemonic (SeedSourceUnenc):

	stdin_ok = True
	fmt_codes = 'mmwords','words','mnemonic','mnem','mn','m'
	desc = 'mnemonic data'
	ext = 'mmwords'
	wl_checksums = {
		'electrum': '5ca31424',
		'tirosh':   '1a5faeff'
	}
	mn_base = 1626
	wordlists = sorted(wl_checksums)
	dfl_wordlist = 'electrum'
	# dfl_wordlist = 'tirosh'

	@staticmethod
	def _mn2hex_pad(mn): return len(mn) * 8 / 3

	@staticmethod
	def _hex2mn_pad(hexnum): return len(hexnum) * 3 / 8

	@staticmethod
	def baseNtohex(base,words,wl,pad=0):
		deconv =  [wl.index(words[::-1][i])*(base**i)
					for i in range(len(words))]
		ret = ('{:0%sx}' % pad).format(sum(deconv))
		return ('','0')[len(ret) % 2] + ret

	@staticmethod
	def hextobaseN(base,hexnum,wl,pad=0):
		num,ret = int(hexnum,16),[]
		while num:
			ret.append(num % base)
			num /= base
		return [wl[n] for n in [0] * (pad-len(ret)) + ret[::-1]]

	@classmethod
	def hex2mn(cls,hexnum,wordlist):
		wl = cls.get_wordlist(wordlist)
		return cls.hextobaseN(cls.mn_base,hexnum,wl,cls._hex2mn_pad(hexnum))

	@classmethod
	def mn2hex(cls,mn,wordlist):
		wl = cls.get_wordlist(wordlist)
		return cls.baseNtohex(cls.mn_base,mn,wl,cls._mn2hex_pad(mn))

	@classmethod
	def get_wordlist(cls,wordlist=None):
		wordlist = wordlist or cls.dfl_wordlist
		if wordlist not in cls.wordlists:
			die(1,"'%s': invalid wordlist.  Valid choices: '%s'" %
				(wordlist,"' '".join(cls.wordlists)))

		return __import__('mmgen.mn_'+wordlist,fromlist=['words']).words.split()

	@classmethod
	def check_wordlist(cls,wlname):

		wl = cls.get_wordlist(wlname)
		Msg('Wordlist: %s\nLength: %i words' % (capfirst(wlname),len(wl)))
		new_chksum = sha256(' '.join(wl)).hexdigest()[:8]

		if (sorted(wl) == wl):
			Msg('List is sorted')
		else:
			die(3,'ERROR: List is not sorted!')

		compare_chksums(
			new_chksum,'generated checksum',
			cls.wl_checksums[wlname],'saved checksum',
			die_on_fail=True)
		Msg('Checksum %s matches' % new_chksum)

	def _format(self):
		wl = self.get_wordlist()
		seed_hex = self.seed.hexdata
		mn = self.hextobaseN(self.mn_base,seed_hex,wl,self._hex2mn_pad(seed_hex))

		ret = self.baseNtohex(self.mn_base,mn,wl,self._mn2hex_pad(mn))
		# Internal error, so just die on fail
		compare_or_die(ret,'recomputed seed',
						seed_hex,'original',e='Internal error')

		self.ssdata.mnemonic = mn
		self.fmt_data = ' '.join(mn) + '\n'

	def _deformat(self):

		mn = self.fmt_data.split()
		wl = self.get_wordlist()

		if len(mn) not in g.mn_lens:
			msg('Invalid mnemonic (%i words).  Allowed numbers of words: %s' %
					(len(mn),', '.join([str(i) for i in g.mn_lens])))
			return False

		for n,w in enumerate(mn,1):
			if w not in wl:
				msg('Invalid mnemonic: word #%s is not in the wordlist' % n)
				return False

		seed_hex = self.baseNtohex(self.mn_base,mn,wl,self._mn2hex_pad(mn))

		ret = self.hextobaseN(self.mn_base,seed_hex,wl,self._hex2mn_pad(seed_hex))

		# Internal error, so just die
		compare_or_die(' '.join(ret),'recomputed mnemonic',
						' '.join(mn),'original',e='Internal error')

		self.seed = Seed(unhexlify(seed_hex))
		self.ssdata.mnemonic = mn

		check_usr_seed_len(self.seed.length)

		return True

	def _filename(self):
		return '%s[%s].%s' % (self.seed.sid,self.seed.length,self.ext)


class SeedFile (SeedSourceUnenc):

	stdin_ok = True
	fmt_codes = 'mmseed','seed','s'
	desc = 'seed data'
	ext = 'mmseed'

	def _format(self):
		b58seed = b58encode_pad(self.seed.data)
		self.ssdata.chksum = make_chksum_6(b58seed)
		self.ssdata.b58seed = b58seed
		self.fmt_data = '%s %s\n' % (
				self.ssdata.chksum,
				split_into_cols(4,b58seed)
			)

	def _deformat(self):
		desc = self.desc
		ld = self.fmt_data.split()

		if not (7 <= len(ld) <= 12): # 6 <= padded b58 data (ld[1:]) <= 11
			msg('Invalid data length (%s) in %s' % (len(ld),desc))
			return False

		a,b = ld[0],''.join(ld[1:])

		if not is_chksum_6(a):
			msg("'%s': invalid checksum format in %s" % (a, desc))
			return False

		if not is_b58string(b):
			msg("'%s': not a base 58 string, in %s" % (b, desc))
			return False

		vmsg_r('Validating %s checksum...' % desc)

		if not compare_chksums(
				a,'checksum',make_chksum_6(b),'base 58 data'):
			return False

		ret = b58decode_pad(b)

		if ret == False:
			msg('Invalid base-58 encoded seed: %s' % val)
			return False

		self.seed = Seed(ret)
		self.ssdata.chksum = a
		self.ssdata.b58seed = b

		check_usr_seed_len(self.seed.length)

		return True

	def _filename(self):
		return '%s[%s].%s' % (self.seed.sid,self.seed.length,self.ext)


class Wallet (SeedSourceEnc):

	fmt_codes = 'wallet','w'
	desc = g.proj_name + ' wallet'
	ext = 'mmdat'

	def _get_label_from_user(self,old_lbl=''):
		d = ("to reuse the label '%s'" % old_lbl.hl()) if old_lbl else 'for no label'
		p = 'Enter a wallet label, or hit ENTER %s: ' % d
		while True:
			msg_r(p)
			ret = my_raw_input('')
			if ret:
				self.ssdata.label = MMGenWalletLabel(ret,on_fail='return')
				if self.ssdata.label:
					break
				else:
					msg('Invalid label.  Trying again...')
			else:
				self.ssdata.label = old_lbl or MMGenWalletLabel('No Label')
				break
		return self.ssdata.label

	# nearly identical to _get_hash_preset() - factor?
	def _get_label(self):
		if hasattr(self,'ss_in') and hasattr(self.ss_in.ssdata,'label'):
			old_lbl = self.ss_in.ssdata.label
			if opt.keep_label:
				qmsg("Reusing label '%s' at user request" % old_lbl.hl())
				self.ssdata.label = old_lbl
			elif opt.label:
				qmsg("Using label '%s' requested on command line" % opt.label.hl())
				lbl = self.ssdata.label = opt.label
			else: # Prompt, using old value as default
				lbl = self._get_label_from_user(old_lbl)

			if (not opt.keep_label) and self.op == 'pwchg_new':
				m = ("changed to '%s'" % lbl,'unchanged')[lbl==old_lbl]
				qmsg('Label %s' % m)
		elif opt.label:
			qmsg("Using label '%s' requested on command line" % opt.label.hl())
			self.ssdata.label = opt.label
		else:
			self._get_label_from_user()

	def _encrypt(self):
		self._get_first_pw_and_hp_and_encrypt_seed()
		self._get_label()
		d = self.ssdata
		d.pw_status = ('NE','E')[len(d.passwd)==0]
		d.timestamp = make_timestamp()

	def _format(self):
		d = self.ssdata
		s = self.seed
		slt_fmt  = b58encode_pad(d.salt)
		es_fmt = b58encode_pad(d.enc_seed)
		lines = (
			d.label,
			'{} {} {} {} {}'.format(s.sid.lower(), d.key_id.lower(),
										s.length, d.pw_status, d.timestamp),
			'{}: {} {} {}'.format(d.hash_preset,*get_hash_params(d.hash_preset)),
			'{} {}'.format(make_chksum_6(slt_fmt),split_into_cols(4,slt_fmt)),
			'{} {}'.format(make_chksum_6(es_fmt), split_into_cols(4,es_fmt))
		)
		chksum = make_chksum_6(' '.join(lines))
		self.fmt_data = '%s\n' % '\n'.join((chksum,)+lines)

	def _deformat(self):

		def check_master_chksum(lines,desc):

			if len(lines) != 6:
				msg('Invalid number of lines (%s) in %s data' %
						(len(lines),desc))
				return False

			if not is_chksum_6(lines[0]):
				msg('Incorrect master checksum (%s) in %s data' %
						(lines[0],desc))
				return False

			chk = make_chksum_6(' '.join(lines[1:]))
			if not compare_chksums(lines[0],'master',chk,'computed',
						hdr='For wallet master checksum'):
				return False

			return True

		lines = self.fmt_data.splitlines()
		if not check_master_chksum(lines,self.desc): return False

		d = self.ssdata
		d.label = MMGenWalletLabel(lines[1])

		d1,d2,d3,d4,d5 = lines[2].split()
		d.seed_id = d1.upper()
		d.key_id  = d2.upper()
		check_usr_seed_len(int(d3))
		d.pw_status,d.timestamp = d4,d5

		hpdata = lines[3].split()

		d.hash_preset = hp = hpdata[0][:-1]  # a string!
		qmsg("Hash preset of wallet: '%s'" % hp)
		if 'hash_preset' in opt.set_by_user:
			uhp = opt.hash_preset
			if uhp != hp:
				qmsg("Warning: ignoring user-requested hash preset '%s'" % uhp)

		hash_params = [int(i) for i in hpdata[1:]]

		if hash_params != get_hash_params(d.hash_preset):
			msg("Hash parameters '%s' don't match hash preset '%s'" %
					(' '.join(hash_params), d.hash_preset))
			return False

		lmin,lmax = b58_lens[0],b58_lens[-1] # 22,33,44
		for i,key in (4,'salt'),(5,'enc_seed'):
			l = lines[i].split(' ')
			chk = l.pop(0)
			b58_val = ''.join(l)

			if len(b58_val) < lmin or len(b58_val) > lmax:
				msg('Invalid format for %s in %s: %s' % (key,self.desc,l))
				return False

			if not compare_chksums(chk,key,
					make_chksum_6(b58_val),'computed checksum'):
				return False

			val = b58decode_pad(b58_val)
			if val == False:
				msg('Invalid base 58 number: %s' % b58_val)
				return False

			setattr(d,key,val)

		return True

	def _decrypt(self):
		d = self.ssdata
		# Needed for multiple transactions with {}-txsign
		suf = ('',self.infile.name)[bool(opt.quiet)]
		self._get_passphrase(desc_suf=suf)
		key = make_key(d.passwd, d.salt, d.hash_preset)
		ret = decrypt_seed(d.enc_seed, key, d.seed_id, d.key_id)
		if ret:
			self.seed = Seed(ret)
			return True
		else:
			return False

	def _filename(self):
		return '{}-{}[{},{}].{}'.format(
				self.seed.sid,
				self.ssdata.key_id,
				self.seed.length,
				self.ssdata.hash_preset,
				self.ext
			)


class Brainwallet (SeedSourceEnc):

	stdin_ok = True
	fmt_codes = 'mmbrain','brainwallet','brain','bw','b'
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
		# Don't set opt.seed_len! In txsign, BW seed len might differ from other seed srcs
		if opt.brain_params:
			seed_len,d.hash_preset = self.get_bw_params()
		else:
			if 'seed_len' not in opt.set_by_user:
				m1 = 'Using default seed length of %s bits'
				m2 = 'If this is not what you want, use the --seed-len option'
				qmsg((m1+'\n'+m2) % yellow(str(opt.seed_len)))
			self._get_hash_preset()
			seed_len = opt.seed_len
		qmsg_r('Hashing brainwallet data.  Please wait...')
		# Use buflen arg of scrypt.hash() to get seed of desired length
		seed = scrypt_hash_passphrase(self.brainpasswd, '',
					d.hash_preset, buflen=seed_len/8)
		qmsg('Done')
		self.seed = Seed(seed)
		msg('Seed ID: %s' % self.seed.sid)
		qmsg('Check this value against your records')
		return True


class IncogWallet (SeedSourceEnc):

	file_mode = 'binary'
	fmt_codes = 'mmincog','incog','icg','i'
	desc = 'incognito data'
	ext = 'mmincog'
	no_tty = True

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
		'dec_chk': " %s hash preset"
	}

	def _make_iv_chksum(self,s): return sha256(s).hexdigest()[:8].upper()

	def _get_incog_data_len(self,seed_len):
		e = (g.hincog_chk_len,0)[bool(opt.old_incog_fmt)]
		return g.aesctr_iv_len + g.salt_len + e + seed_len/8

	def _incog_data_size_chk(self):
		# valid sizes: 56, 64, 72
		dlen = len(self.fmt_data)
		valid_dlen = self._get_incog_data_len(opt.seed_len)
		if dlen == valid_dlen:
			return True
		else:
			if opt.old_incog_fmt:
				msg('WARNING: old-style incognito format requested.  ' +
					'Are you sure this is correct?')
			msg(('Invalid incognito data size (%s bytes) for this ' +
				'seed length (%s bits)') % (dlen,opt.seed_len))
			msg('Valid data size for this seed length: %s bytes' % valid_dlen)
			for sl in g.seed_lens:
				if dlen == self._get_incog_data_len(sl):
					die(1,'Valid seed length for this data size: %s bits' % sl)
			msg(('This data size (%s bytes) is invalid for all available ' +
				'seed lengths') % dlen)
			return False

	def _encrypt (self):
		self._get_first_pw_and_hp_and_encrypt_seed()
		if opt.old_incog_fmt:
			die(1,'Writing old-format incog wallets is unsupported')
		d = self.ssdata
		# IV is used BOTH to initialize counter and to salt password!
		d.iv = get_random(g.aesctr_iv_len)
		d.iv_id = self._make_iv_chksum(d.iv)
		msg('New Incog Wallet ID: %s' % d.iv_id)
		qmsg('Make a record of this value')
		vmsg(self.msg['record_incog_id'])

		d.salt = get_random(g.salt_len)
		key = make_key(d.passwd, d.salt, d.hash_preset, 'incog wallet key')
		chk = sha256(self.seed.data).digest()[:8]
		d.enc_seed = encrypt_data(chk + self.seed.data, key, 1, 'seed')

		d.wrapper_key = make_key(d.passwd, d.iv, d.hash_preset, 'incog wrapper key')
		d.key_id = make_chksum_8(d.wrapper_key)
		vmsg('Key ID: %s' % d.key_id)
		d.target_data_len = self._get_incog_data_len(self.seed.length)

	def _format(self):
		d = self.ssdata
#		print len(d.iv), len(d.salt), len(d.enc_seed), len(d.wrapper_key)
		self.fmt_data = d.iv + encrypt_data(
							d.salt + d.enc_seed,
							d.wrapper_key,
							int(hexlify(d.iv),16),
							self.desc)
#		print len(self.fmt_data)

	def _filename(self):
		s = self.seed
		d = self.ssdata
		return '{}-{}-{}[{},{}].{}'.format(
				s.sid,
				d.key_id,
				d.iv_id,
				s.length,
				d.hash_preset,
				self.ext)

	def _deformat(self):

		if not self._incog_data_size_chk(): return False

		d = self.ssdata
		d.iv             = self.fmt_data[0:g.aesctr_iv_len]
		d.incog_id       = self._make_iv_chksum(d.iv)
		d.enc_incog_data = self.fmt_data[g.aesctr_iv_len:]
		msg('Incog Wallet ID: %s' % d.incog_id)
		qmsg('Check this value against your records')
		vmsg(self.msg['check_incog_id'])

		return True

	def _verify_seed_newfmt(self,data):
		chk,seed = data[:8],data[8:]
		if sha256(seed).digest()[:8] == chk:
			qmsg('Passphrase%s are correct' % (self.msg['dec_chk'] % 'and'))
			return seed
		else:
			msg('Incorrect passphrase%s' % (self.msg['dec_chk'] % 'or'))
			return False

	def _verify_seed_oldfmt(self,seed):
		m = 'Seed ID: %s.  Is the Seed ID correct?' % make_chksum_8(seed)
		if keypress_confirm(m, True):
			return seed
		else:
			return False

	def _decrypt(self):
		d = self.ssdata
		self._get_hash_preset(desc_suf=d.incog_id)
		self._get_passphrase(desc_suf=d.incog_id)

		# IV is used BOTH to initialize counter and to salt password!
		key = make_key(d.passwd, d.iv, d.hash_preset, 'wrapper key')
		dd = decrypt_data(d.enc_incog_data, key,
				int(hexlify(d.iv),16), 'incog data')

		d.salt     = dd[0:g.salt_len]
		d.enc_seed = dd[g.salt_len:]

		key = make_key(d.passwd, d.salt, d.hash_preset, 'main key')
		qmsg('Key ID: %s' % make_chksum_8(key))

		verify_seed = getattr(self,'_verify_seed_'+
						('newfmt','oldfmt')[bool(opt.old_incog_fmt)])

		seed = verify_seed(decrypt_seed(d.enc_seed, key, '', ''))

		if seed:
			self.seed = Seed(seed)
			msg('Seed ID: %s' % self.seed.sid)
			return True
		else:
			return False


class IncogWalletHex (IncogWallet):

	file_mode = 'text'
	desc = 'hex incognito data'
	fmt_codes = 'mmincox','incox','incog_hex','xincog','ix','xi'
	ext = 'mmincox'
	no_tty = False

	def _deformat(self):
		ret = decode_pretty_hexdump(self.fmt_data)
		if ret:
			self.fmt_data = ret
			return IncogWallet._deformat(self)
		else:
			return False

	def _format(self):
		IncogWallet._format(self)
		self.fmt_data = pretty_hexdump(self.fmt_data)


class IncogWalletHidden (IncogWallet):

	desc = 'hidden incognito data'
	fmt_codes = 'incog_hidden','hincog','ih','hi'
	ext = None

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
		'dec_chk': ', hash preset, offset %s seed length'
	}


	def _get_hincog_params(self,wtype):
		p = getattr(opt,'hidden_incog_'+ wtype +'_params')
		a,b = p.split(',')
		return a,int(b)

	def _check_valid_offset(self,fn,action):
		d = self.ssdata
		m = ('Input','Destination')[action=='write']
		if fn.size < d.hincog_offset + d.target_data_len:
			die(1,
	"%s file '%s' has length %s, too short to %s %s bytes of data at offset %s"
				% (m,fn.name,fn.size,action,d.target_data_len,d.hincog_offset))

	def _get_data(self):
		d = self.ssdata
		d.hincog_offset = self._get_hincog_params('input')[1]

		qmsg("Getting hidden incog data from file '%s'" % self.infile.name)

		# Already sanity-checked:
		d.target_data_len = self._get_incog_data_len(opt.seed_len)
		self._check_valid_offset(self.infile,'read')

		flgs = os.O_RDONLY|os.O_BINARY if g.platform == 'win' else os.O_RDONLY
		fh = os.open(self.infile.name,flgs)
		os.lseek(fh,int(d.hincog_offset),os.SEEK_SET)
		self.fmt_data = os.read(fh,d.target_data_len)
		os.close(fh)
		qmsg("Data read from file '%s' at offset %s" %
				(self.infile.name,d.hincog_offset), 'Data read from file')

	# overrides method in SeedSource
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
			if keypress_confirm("Requested file '%s' does not exist.  Create?"
					% fn, default_yes=True):
				min_fsize = d.target_data_len + d.hincog_offset
				msg(self.msg['choose_file_size'].format(min_fsize))
				while True:
					fsize = parse_nbytes(my_raw_input('Enter file size: '))
					if fsize >= min_fsize: break
					msg('File size must be an integer no less than %s' %
							min_fsize)

				from mmgen.tool import rand2file
				rand2file(fn, str(fsize))
				check_offset = False
			else:
				die(1,'Exiting at user request')

		f = Filename(fn,ftype=type(self),write=True)

		dmsg('%s data len %s, offset %s' % (
				capfirst(self.desc),d.target_data_len,d.hincog_offset))

		if check_offset:
			self._check_valid_offset(f,'write')
			if not opt.quiet: confirm_or_exit('',"alter file '%s'" % f.name)

		flgs = os.O_RDWR|os.O_BINARY if g.platform == 'win' else os.O_RDWR
		fh = os.open(f.name,flgs)
		os.lseek(fh, int(d.hincog_offset), os.SEEK_SET)
		os.write(fh, self.fmt_data)
		os.close(fh)
		msg("%s written to file '%s' at offset %s" % (
				capfirst(self.desc),f.name,d.hincog_offset))

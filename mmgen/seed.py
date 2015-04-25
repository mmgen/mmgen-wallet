#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
import sys,os
from binascii import hexlify,unhexlify

import mmgen.globalvars as g
import mmgen.opt as opt
from mmgen.bitcoin import b58encode_pad,b58decode_pad,b58_lens
from mmgen.obj import *
from mmgen.filename import *
from mmgen.util import *
from mmgen.crypto import *

pnm = g.proj_name

def check_usr_seed_len(seed_len):
	if opt.seed_len != seed_len and 'seed_len' in opt.set_by_user:
		m = "ERROR: requested seed length (%s) " + \
			"doesn't match seed length of source (%s)"
		die(1, m % (opt.seed_len,seed_len))


class Seed(MMGenObject):
	def __init__(self,seed_bin=None):
		if not seed_bin:
			# Truncate random data for smaller seed lengths
			seed_bin = sha256(get_random(1033)).digest()[:opt.seed_len/8]
		elif len(seed_bin)*8 not in g.seed_lens:
			die(3,"%s: invalid seed length" % len(seed_bin))

		self.data      = seed_bin
		self.hexdata   = hexlify(seed_bin)
		self.sid       = make_chksum_8(seed_bin)
		self.length    = len(seed_bin) * 8


class SeedSource(MMGenObject):

	desc = g.proj_name + " seed source"
	stdin_ok = False
	ask_tty = True
	no_tty  = False
	_msg = {}

	class SeedSourceData(MMGenObject): pass

	def __new__(cls,fn=None,ss=None,ignore_in_fmt_opt=False):

		def die_on_opt_mismatch(opt,sstype):
			opt_sstype = cls.fmt_code_to_sstype(opt)
			compare_or_die(
				opt_sstype.__name__, "input format specified on command line",
				sstype.__name__,     "input file format"
			)

		if ss:
			sstype = cls.fmt_code_to_sstype(opt.out_fmt)
			me = super(cls,cls).__new__(sstype or Wallet) # output default: Wallet
			me.seed = ss.seed
			me.ss_in = ss
		elif fn or opt.hidden_incog_input_params:
			if fn:
				f = Filename(fn)
				sstype = cls.ext_to_sstype(f.ext)
			else:
				fn = opt.hidden_incog_input_params.split(",")[0]
				f  = Filename(fn,ftype="hincog")
				sstype = cls.fmt_code_to_sstype("hincog")

			if opt.in_fmt and not ignore_in_fmt_opt:
				die_on_opt_mismatch(opt.in_fmt,sstype)

			me = super(cls,cls).__new__(sstype)
			me.infile = f
		elif opt.in_fmt:  # Input format
			sstype = cls.fmt_code_to_sstype(opt.in_fmt)
			me = super(cls,cls).__new__(sstype)
		else: # Called with no inputs - initialize with random seed
			sstype = cls.fmt_code_to_sstype(opt.out_fmt)
			me = super(cls,cls).__new__(sstype or Wallet) # output default: Wallet
			me.seed = Seed()

		return me

	def __init__(self,fn=None,ss=None,ignore_in_fmt_opt=False):

		self.ssdata = self.SeedSourceData()
		self.msg = {}

		for c in reversed(self.__class__.__mro__):
			if hasattr(c,'_msg'):
				self.msg.update(c._msg)

		if hasattr(self,'seed'):
			g.use_urandchars = True
			self._encrypt()
		elif hasattr(self,'infile'):
			self._deformat_once()
			self._decrypt_retry()
		else:
			if not self.stdin_ok:
				die(1,"Reading from standard input not supported for %s format"
						% self.desc)
			self._deformat_retry()
			self._decrypt_retry()

	def _get_data(self):
		if hasattr(self,'infile'):
			self.fmt_data = get_data_from_file(self.infile.name,self.desc)
		else:
			self.fmt_data = get_data_from_user(self.desc)

	def _deformat_once(self):
		self._get_data()
		if not self._deformat():
			die(2,"Invalid format for input data")

	def _deformat_retry(self):
		while True:
			self._get_data()
			if self._deformat(): break
			msg("Trying again...")

	def _decrypt_retry(self):
		while True:
			if self._decrypt(): break
			msg("Trying again...")

	subclasses = []

	@classmethod
	def _get_subclasses(cls):

		if cls.subclasses: return cls.subclasses

		ret,gl = [],globals()
		for c in [gl[k] for k in gl]:
			try:
				if issubclass(c,cls):
					ret.append(c)
			except:
				pass

		cls.subclasses = ret
		return ret

	@classmethod
	def fmt_code_to_sstype(cls,fmt_code):
		if not fmt_code: return None
		for c in cls._get_subclasses():
			if hasattr(c,"fmt_codes") and fmt_code in c.fmt_codes:
				return c
		return None

	@classmethod
	def ext_to_sstype(cls,ext):
		if not ext: return None
		for c in cls._get_subclasses():
			if hasattr(c,"ext") and ext == c.ext:
				return c
		return None

	@classmethod
	def format_fmt_codes(cls):
		d = [(c.__name__,",".join(c.fmt_codes)) for c in cls._get_subclasses()
				if hasattr(c,"fmt_codes")]
		w = max([len(a) for a,b in d])
		ret = ["{:<{w}}  {}".format(a,b,w=w) for a,b in [
			("Format","Valid codes"),
			("------","-----------")
			] + sorted(d)]
		return "\n".join(ret) + "\n"

	def write_to_file(self):
		self._format()
		kwargs = {
			'desc':     self.desc,
			'ask_tty':  self.ask_tty,
			'no_tty':   self.no_tty
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

	def _get_pw(self,desc=None):
		self.ssdata.passwd = get_mmgen_passphrase(desc)

	def _get_hash_preset(self,desc=None):
		# Converting:
		desc = desc or self.desc
		if hasattr(self,'ss_in') and hasattr(self.ss_in.ssdata,'hash_preset'):
			if opt.keep_hash_preset:
				a = self.ss_in.ssdata.hash_preset
				qmsg("Reusing hash preset '%s' as per user request" % a)
			elif 'hash_preset' in opt.set_by_user:
				# Prompt, but use user-requested value as default
				a = get_hash_preset_from_user(hp=opt.hash_preset,desc=desc)
			else:
				a = get_hash_preset_from_user(desc=desc)
		elif 'hash_preset' in opt.set_by_user:
			a = opt.hash_preset
			qmsg("Using user-requested hash preset of '%s'" % a)
		else:
			a = get_hash_preset_from_user(desc=self.desc)
		self.ssdata.hash_preset = a

	def _get_first_pw_and_hp_and_encrypt_seed(self):
		d = self.ssdata

		if hasattr(self,'ss_in') and hasattr(self.ss_in.ssdata,'passwd') \
				and opt.keep_passphrase:
			d.passwd = self.ss_in.ssdata.passwd
			qmsg("Reusing passphrase as per user request")

		self._get_hash_preset(desc="new " + self.desc)

		if not hasattr(d,'passwd'):
			qmsg(self.msg['choose_passphrase'] % (self.desc,self.ssdata.hash_preset))
			d.passwd = get_new_passphrase(desc="new " + self.desc)

		d.salt     = sha256(get_random(128)).digest()[:g.salt_len]
		key        = make_key(d.passwd, d.salt, d.hash_preset)
		d.key_id   = make_chksum_8(key)
		d.enc_seed = encrypt_seed(self.seed.data,key)


class Mnemonic (SeedSourceUnenc):

	stdin_ok = True
	fmt_codes = "mmwords","words","mnemonic","mnem","mn","m"
	desc = "mnemonic data"
	ext = "mmwords"
	wl_checksums = {
		"electrum": '5ca31424',
		"tirosh":   '1a5faeff'
	}
	mn_base = 1626
	wordlists = sorted(wl_checksums)

	def _mn2hex_pad(self,mn): return len(mn) * 8 / 3
	def _hex2mn_pad(self,hexnum): return len(hexnum) * 3 / 8

	def _baseNtohex(self,base,words,wl,pad=0):
		deconv =  [wl.index(words[::-1][i])*(base**i)
					for i in range(len(words))]
		ret = ("{:0%sx}" % pad).format(sum(deconv))
		return "%s%s" % (('0' if len(ret) % 2 else ''), ret)

	def _hextobaseN(self,base,hexnum,wl,pad=0):
		num,ret = int(hexnum,16),[]
		while num:
			ret.append(num % base)
			num /= base
		return [wl[n] for n in [0] * (pad-len(ret)) + ret[::-1]]

	def _get_wordlist(self,wordlist=g.default_wordlist):
		wordlist = wordlist.lower()
		if wordlist not in self.wordlists:
			die(1,'"%s": invalid wordlist.  Valid choices: %s' %
				(wordlist,'"'+'" "'.join(self.wordlists)+'"'))

		if wordlist == "electrum":
			from mmgen.mn_electrum  import words
		elif wordlist == "tirosh":
			from mmgen.mn_tirosh    import words
		else:
			die(3,"Internal error: unknown wordlist")

		return words.strip().split("\n")

	def _format(self):
		wl = self._get_wordlist()
		seed_hex = self.seed.hexdata
		mn = self._hextobaseN(self.mn_base,seed_hex,wl,self._hex2mn_pad(seed_hex))

		ret = self._baseNtohex(self.mn_base,mn,wl,self._mn2hex_pad(mn))
		# Internal error, so just die on fail
		compare_or_die(ret,"recomputed seed",
						seed_hex,"original",e="Internal error")

		self.ssdata.mnemonic = mn
		self.fmt_data = " ".join(mn) + "\n"

	def _deformat(self):

		mn = self.fmt_data.split()
		wl = self._get_wordlist()

		if len(mn) not in g.mn_lens:
			msg("Invalid mnemonic (%i words).  Allowed numbers of words: %s" %
					(len(mn),", ".join([str(i) for i in g.mn_lens])))
			return False

		for n,w in enumerate(mn,1):
			if w not in wl:
				msg("Invalid mnemonic: word #%s is not in the wordlist" % n)
				return False

		seed_hex = self._baseNtohex(self.mn_base,mn,wl,self._mn2hex_pad(mn))

		ret = self._hextobaseN(self.mn_base,seed_hex,wl,self._hex2mn_pad(seed_hex))

		# Internal error, so just die
		compare_or_die(" ".join(ret),"recomputed mnemonic",
						" ".join(mn),"original",e="Internal error")

		self.seed = Seed(unhexlify(seed_hex))
		self.ssdata.mnemonic = mn

		check_usr_seed_len(self.seed.length)

		qmsg("Valid mnemonic for seed ID %s" % make_chksum_8(self.seed.data))
		return True

	def _filename(self):
		return "%s[%s].%s" % (self.seed.sid,self.seed.length,self.ext)


class SeedFile (SeedSourceUnenc):

	stdin_ok = True
	fmt_codes = "mmseed","seed","s"
	desc = "seed data"
	ext = "mmseed"

	def _format(self):
		b58seed = b58encode_pad(self.seed.data)
		self.ssdata.chksum = make_chksum_6(b58seed)
		self.ssdata.b58seed = b58seed
		self.fmt_data = "%s %s\n" % (
				self.ssdata.chksum,
				split_into_cols(4,b58seed)
			)

	def _deformat(self):
		desc = self.desc
		ld = self.fmt_data.split()

		if not (7 <= len(ld) <= 12): # 6 <= padded b58 data (ld[1:]) <= 11
			msg("Invalid data length (%s) in %s" % (len(ld),desc))
			return False

		a,b = ld[0],"".join(ld[1:])

		if not is_chksum_6(a):
			msg("'%s': invalid checksum format in %s" % (a, desc))
			return False

		if not is_b58string(b):
			msg("'%s': not a base 58 string, in %s" % (b, desc))
			return False

		vmsg_r("Validating %s checksum..." % desc)

		if not compare_chksums(
				a,"checksum",make_chksum_6(b),"base 58 data"):
			return False

		ret = b58decode_pad(b)

		if ret == False:
			msg("Invalid base-58 encoded seed: %s" % val)
			return False

		self.seed = Seed(ret)
		self.ssdata.chksum = a
		self.ssdata.b58seed = b

		check_usr_seed_len(self.seed.length)

		qmsg("Valid seed data for seed ID %s" % make_chksum_8(self.seed.data))

		return True

	def _filename(self):
		return "%s[%s].%s" % (self.seed.sid,self.seed.length,self.ext)


class Wallet (SeedSourceEnc):

	fmt_codes = "wallet","w"
	desc = g.proj_name + " wallet"
	ext = "mmdat"

	def _encrypt(self):
		self._get_first_pw_and_hp_and_encrypt_seed()
		d = self.ssdata
		d.label = opt.label or "No Label"
		d.pw_status = "NE" if len(d.passwd) else "E"
		d.timestamp = make_timestamp()

	def _format(self):
		d = self.ssdata
		s = self.seed
		slt_fmt  = b58encode_pad(d.salt)
		es_fmt = b58encode_pad(d.enc_seed)
		lines = (
			d.label,
			"{} {} {} {} {}".format(s.sid.lower(), d.key_id.lower(),
										s.length, d.pw_status, d.timestamp),
			"{}: {} {} {}".format(d.hash_preset,*get_hash_params(d.hash_preset)),
			"{} {}".format(make_chksum_6(slt_fmt),split_into_cols(4,slt_fmt)),
			"{} {}".format(make_chksum_6(es_fmt), split_into_cols(4,es_fmt))
		)
		chksum = make_chksum_6(" ".join(lines))
		self.fmt_data = "%s\n" % "\n".join((chksum,)+lines)

	def _deformat(self):

		def check_master_chksum(lines,desc):

			if len(lines) != 6:
				msg("Invalid number of lines (%s) in %s data" %
						(len(lines),desc))
				return False

			if not is_chksum_6(lines[0]):
				msg("Incorrect master checksum (%s) in %s data" %
						(lines[0],desc))
				return False

			chk = make_chksum_6(" ".join(lines[1:]))
			if not compare_chksums(lines[0],"master",chk,"computed",
						hdr="For wallet master checksum"):
				return False

			return True

		lines = self.fmt_data.rstrip().split("\n")
		if not check_master_chksum(lines,self.desc): return False

		d = self.ssdata
		d.label = lines[1]

		d1,d2,d3,d4,d5 = lines[2].split()
		d.seed_id = d1.upper()
		d.key_id  = d2.upper()
		check_usr_seed_len(int(d3))
		d.pw_status,d.timestamp = d4,d5

		hpdata = lines[3].split()

		d.hash_preset = hp = hpdata[0][:-1]  # a string!
		qmsg("Hash preset of wallet: '%s'" % hp)
		uhp = opt.hash_preset
		if uhp and 'hash_preset' in opt.set_by_user and uhp != hp:
			msg("Warning: ignoring user-requested hash preset '%s'" % uhp)

		hash_params = [int(i) for i in hpdata[1:]]

		if hash_params != get_hash_params(d.hash_preset):
			msg("Hash parameters '%s' don't match hash preset '%s'" %
					(" ".join(hash_params), d.hash_preset))
			return False

		lmin,lmax = b58_lens[0],b58_lens[-1] # 22,33,44
		for i,key in (4,"salt"),(5,"enc_seed"):
			l = lines[i].split(" ")
			chk = l.pop(0)
			b58_val = "".join(l)

			if len(b58_val) < lmin or len(b58_val) > lmax:
				msg("Invalid format for %s in %s: %s" % (key,self.desc,l))
				return False

			if not compare_chksums(chk,key,
					make_chksum_6(b58_val),"computed checksum"):
				return False

			val = b58decode_pad(b58_val)
			if val == False:
				msg("Invalid base 58 number: %s" % b58_val)
				return False

			setattr(d,key,val)

		return True

	def _decrypt(self):
		d = self.ssdata
		# Needed for multiple transactions with {}-txsign
		add = " "+self.infile.name if opt.quiet else ""
		self._get_pw(self.desc+add)
		key = make_key(d.passwd, d.salt, d.hash_preset)
		ret = decrypt_seed(d.enc_seed, key, d.seed_id, d.key_id)
		if ret:
			self.seed = Seed(ret)
			return True
		else:
			return False

	def _filename(self):
		return "{}-{}[{},{}].{}".format(
				self.seed.sid,
				self.ssdata.key_id,
				self.seed.length,
				self.ssdata.hash_preset,
				self.ext
			)

# 	def __str__(self):
##	label,metadata,hash_preset,salt,enc_seed):
# 		d = self.ssdata
# 		s = self.seed
# 		out = ["WALLET DATA"]
# 		fs = "  {:18} {}"
# 		pw_empty = "Yes" if d.metadata[3] == "E" else "No"
# 		for i in (
# 			("Label:",         d.label),
# 			("Seed ID:",       s.sid),
# 			("Key  ID:",       d.key_id),
# 			("Seed length:",   "%s bits (%s bytes)" % (s.length,s.length/8)),
# 			("Scrypt params:", "Preset '%s' (%s)" % (opt.hash_preset,
# 					" ".join([str(i) for i in get_hash_params(opt.hash_preset)])
# 					)
# 			),
# 			("Passphrase empty?", pw_empty),
# 			("Timestamp:",     "%s UTC" % d.metadata[4]),
# 		): out.append(fs.format(*i))
#
# 		fs = "  {:6} {}"
# 		for i in (
# 			("Salt:",   ""),
# 			("  b58:",  b58encode_pad(d.salt)),
# 			("  hex:",  hexlify(d.salt)),
# 			("Encrypted seed:", ""),
# 			("  b58:",  b58encode_pad(d.enc_seed)),
# 			("  hex:",  hexlify(d.enc_seed))
# 		): out.append(fs.format(*i))
#
# 		return "\n".join(out)


class Brainwallet (SeedSourceEnc):

	stdin_ok = True
	fmt_codes = "mmbrain","brainwallet","brain","bw","b"
	desc = "brainwallet"
	ext = "mmbrain"

	def _deformat(self):
		self.brainpasswd = " ".join(self.fmt_data.split())
		return True

	def _decrypt(self):
		self._get_hash_preset()
		vmsg_r("Hashing brainwallet data.  Please wait...")
		# Use buflen arg of scrypt.hash() to get seed of desired length
		seed = scrypt_hash_passphrase(self.brainpasswd, "",
					self.ssdata.hash_preset, buflen=opt.seed_len/8)
		vmsg("Done")
		self.seed = Seed(seed)
		msg("Seed ID: %s" % self.seed.sid)
		qmsg("Check this value against your records")
		return True


class IncogWallet (SeedSourceEnc):

	fmt_codes = "mmincog","incog","icg","i"
	desc = "incognito data"
	ext = "mmincog"
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
If the seed ID above is correct but you're seeing this message, then you need
to exit and re-run the program with the '--old-incog-fmt' option.
""".strip(),
		'dec_chk': " %s hash preset"
	}

	def _make_iv_chksum(self,s): return sha256(s).hexdigest()[:8].upper()

	def _get_incog_data_len(self,seed_len):
		e = 0 if opt.old_incog_fmt else g.hincog_chk_len
		return g.aesctr_iv_len + g.salt_len + e + seed_len/8

	def _incog_data_size_chk(self):
		# valid sizes: 56, 64, 72
		dlen = len(self.fmt_data)
		valid_dlen = self._get_incog_data_len(opt.seed_len)
		if dlen == valid_dlen:
			return True
		else:
			if opt.old_incog_fmt:
				msg("WARNING: old-style incognito format requested.  " +
					"Are you sure this is correct?")
			msg(("Invalid incognito data size (%s bytes) for this " +
				"seed length (%s bits)") % (dlen,opt.seed_len))
			msg("Valid data size for this seed length: %s bytes" % valid_dlen)
			for sl in g.seed_lens:
				if dlen == self._get_incog_data_len(sl):
					die(1,"Valid seed length for this data size: %s bits" % sl)
			msg(("This data size (%s bytes) is invalid for all available " +
				"seed lengths") % dlen)
			return False

	def _encrypt (self):
		self._get_first_pw_and_hp_and_encrypt_seed()
		if opt.old_incog_fmt:
			die(1,"Writing old-format incog wallets is unsupported")
		d = self.ssdata
		# IV is used BOTH to initialize counter and to salt password!
		d.iv = get_random(g.aesctr_iv_len)
		d.iv_id = self._make_iv_chksum(d.iv)
		msg("New Incog Wallet ID: %s" % d.iv_id)
		qmsg("Make a record of this value")
		vmsg(self.msg['record_incog_id'])

		d.salt = get_random(g.salt_len)
		key = make_key(d.passwd, d.salt, d.hash_preset, "incog wallet key")
		chk = sha256(self.seed.data).digest()[:8]
		d.enc_seed = encrypt_data(chk + self.seed.data, key, 1, "seed")

		d.wrapper_key = make_key(d.passwd, d.iv, d.hash_preset, "incog wrapper key")
		d.key_id = make_chksum_8(d.wrapper_key)
		vmsg("Key ID: %s" % d.key_id)
		d.target_data_len = self._get_incog_data_len(self.seed.length)

	def _format(self):
		d = self.ssdata
		self.fmt_data = d.iv + encrypt_data(
							d.salt + d.enc_seed,
							d.wrapper_key,
							int(hexlify(d.iv),16),
							self.desc
						)

	def _filename(self):
		s = self.seed
		d = self.ssdata
		return "{}-{}-{}[{},{}].{}".format(
				s.sid,
				d.key_id,
				d.iv_id,
				s.length,
				d.hash_preset,
				self.ext
			)

	def _deformat(self):

		if not self._incog_data_size_chk(): return False

		d = self.ssdata
		d.iv             = self.fmt_data[0:g.aesctr_iv_len]
		d.incog_id       = self._make_iv_chksum(d.iv)
		d.enc_incog_data = self.fmt_data[g.aesctr_iv_len:]
		msg("Incog Wallet ID: %s" % d.incog_id)
		qmsg("Check this value against your records")
		vmsg(self.msg['check_incog_id'])

		return True

	def _verify_seed_newfmt(self,data):
		chk,seed = data[:8],data[8:]
		if sha256(seed).digest()[:8] == chk:
			qmsg("Passphrase%s are correct" % (self.msg['dec_chk'] % "and"))
			return seed
		else:
			msg("Incorrect passphrase%s" % (self.msg['dec_chk'] % "or"))
			return False

	def _verify_seed_oldfmt(self,seed):
		m = "Seed ID: %s.  Is the seed ID correct?" % make_chksum_8(seed)
		if keypress_confirm(m, True):
			return seed
		else:
			return False

	def _decrypt(self):
		d = self.ssdata
		desc = self.desc+" "+d.incog_id
		self._get_hash_preset(desc)
		self._get_pw(desc)

		# IV is used BOTH to initialize counter and to salt password!
		key = make_key(d.passwd, d.iv, d.hash_preset, "wrapper key")
		dd = decrypt_data(d.enc_incog_data, key,
				int(hexlify(d.iv),16), "incog data")

		d.salt     = dd[0:g.salt_len]
		d.enc_seed = dd[g.salt_len:]

		key = make_key(d.passwd, d.salt, d.hash_preset, "main key")
		msg("Key ID: %s" % make_chksum_8(key))

		verify_seed = self._verify_seed_oldfmt if opt.old_incog_fmt else \
						self._verify_seed_newfmt

		seed = verify_seed(decrypt_seed(d.enc_seed, key, "", ""))

		if seed:
			self.seed = Seed(seed)
			msg("Seed ID: %s" % self.seed.sid)
			return True
		else:
			return False


class IncogWalletHex (IncogWallet):

	desc = "hex incognito data"
	fmt_codes = "mmincox","incog_hex","xincog","ix","xi"
	ext = "mmincox"
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

	desc = "hidden incognito data"
	fmt_codes = "incog_hidden","hincog","ih","hi"
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
		'dec_chk': ", hash preset, offset %s seed length"
	}


	def _get_hincog_params(self,wtype):
		p = getattr(opt,'hidden_incog_'+ wtype +'_params')
		a,b = p.split(",")
		return a,int(b)

	def _check_valid_offset(self,fn,action):
		d = self.ssdata
		m = "Destination" if action == "write" else "Input"
		if fn.size < d.hincog_offset + d.target_data_len:
			die(1,
	"%s file has length %s, too short to %s %s bytes of data at offset %s"
				% (m,fn.size,action,d.target_data_len,d.hincog_offset))

	def _get_data(self):
		d = self.ssdata
		d.hincog_offset = self._get_hincog_params("input")[1]

		qmsg("Getting hidden incog data from file '%s'" % self.infile.name)

		# Already sanity-checked:
		d.target_data_len = self._get_incog_data_len(opt.seed_len)
		self._check_valid_offset(self.infile,"read")

		fh = os.open(self.infile.name,os.O_RDONLY)
		os.lseek(fh,int(d.hincog_offset),os.SEEK_SET)
		self.fmt_data = os.read(fh,d.target_data_len)
		os.close(fh)
		qmsg("Data read from file '%s' at offset %s" %
				(self.infile.name,d.hincog_offset), "Data read from file")


	# overrides method in SeedSource
	def write_to_file(self):
		d = self.ssdata
		self._format()
		compare_or_die(d.target_data_len, "target data length",
				len(self.fmt_data),"length of formatted " + self.desc)
		fn,d.hincog_offset = self._get_hincog_params("output")

		self.hincog_data_is_new = False
		try:
			os.stat(fn)
		except:
			if keypress_confirm("Requested file '%s' does not exist.  Create?"
					% fn, default_yes=True):
				min_fsize = d.target_data_len + d.hincog_offset
				msg(self.msg['choose_file_size'].format(min_fsize))
				while True:
					fsize = my_raw_input("Enter file size: ")
					if is_int(fsize) and int(fsize) >= min_fsize: break
					msg("File size must be an integer no less than %s" %
							min_fsize)

				from mmgen.tool import rand2file
				rand2file(fn, str(fsize))
				self.hincog_data_is_new = True
			else:
				die(1,"Exiting at user request")

		self.outfile = f = Filename(fn,ftype="hincog")

		dmsg("Incog data len %s, offset %s" % (d.target_data_len,d.hincog_offset))

		if not self.hincog_data_is_new:
			self._check_valid_offset(f,"write")
			if not opt.quiet: confirm_or_exit("","alter file '%s'" % f.name)

		fh = os.open(f.name,os.O_RDWR)
		os.lseek(fh, int(d.hincog_offset), os.SEEK_SET)
		os.write(fh, self.fmt_data)
		os.close(fh)
		msg("%s written to file '%s' at offset %s" % (
				self.desc[0].upper()+self.desc[1:],
				f.name,d.hincog_offset))

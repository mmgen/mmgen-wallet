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
from mmgen.obj import *
from mmgen.filename import *
from mmgen.util import *
from mmgen.bitcoin import b58encode_pad,b58decode_pad
from mmgen.crypto import *

pnm = g.proj_name

class Seed(MMGenObject):
	def __init__(self,seed_bin=None):
		if not seed_bin:
			from mmgen.crypto import get_random
			# Truncate random data for smaller seed lengths
			seed_bin = sha256(get_random(1033)).digest()[:opt.seed_len/8]
		elif len(seed_bin)*8 not in g.seed_lens:
			die(3,"%s: invalid seed length" % len(seed_bin))

		self.data      = seed_bin
		self.hexdata   = hexlify(seed_bin)
		self.sid       = make_chksum_8(seed_bin)
		self.len_bytes = len(seed_bin)
		self.len_bits  = len(seed_bin) * 8

class SeedSource(MMGenObject):

	class SeedSourceData(MMGenObject): pass

	desc = "seed source"

	def __init__(self,fn=None,seed=None,passwd=None):

		self.ssdata = self.SeedSourceData()
		self.ssdata.passwd = passwd

		if seed:
			self.desc = "new " + self.desc
			self.seed = seed
			self._pre_encode()
			self._encode()
		else:
			self._get_formatted_data(fn)
			self._deformat()
			self._decode()

	def _get_formatted_data(self,fn):
		if fn:
			self.infile = fn
			self.fmt_data = get_data_from_file(fn.name,self.desc)
		else:
			self.infile = None
			self.fmt_data = get_data_from_user(self.desc)

	def _pre_encode(self): pass

	def init(cls,infile=None,seed=None,passwd=None):

		sstype = None

		if seed:
			if opt.out_fmt:
				sstype = fmt_code_to_sstype(opt.out_fmt)
			# Output format defaults to "Wallet"
			return globals()[sstype or "Wallet"](seed=seed,passwd=passwd)
		else:
			if infile:
				fn = Filename(infile)
				return globals()[fn.sstype](fn=fn,passwd=passwd)
			elif opt.in_fmt:  # Input format
				sstype = fmt_code_to_sstype(opt.in_fmt)
				return globals()[sstype](passwd=passwd)
			else:
				die(2,"Either an input file or input format must be specified")

	init = classmethod(init)

	def write_to_file(self):
		self._format()
		write_to_file_or_stdout(self._filename(),self.fmt_data, self.desc)

class SeedSourceUnenc(SeedSource): pass

class SeedSourceEnc(SeedSource):

	_ss_enc_msg = {
		'choose_passphrase': """
You must choose a passphrase to encrypt your new %s with.
A key will be generated from your passphrase using a hash preset of '%s'.
Please note that no strength checking of passphrases is performed.  For an
empty passphrase, just hit ENTER twice.
	""".strip()
	}

	def _pre_encode(self):
		if self.ssdata.passwd == None: self._get_first_passwd()
		self._get_hash_preset()
		self._encrypt_seed()

	def _get_first_passwd(self):
		qmsg(self._ss_enc_msg['choose_passphrase'] % (self.desc,opt.hash_preset))
		self.ssdata.passwd = get_new_passphrase(what=self.desc)

	def _get_hash_preset(self):
		self.ssdata.hash_preset = \
			opt.hash_preset or get_hash_preset_from_user(what=self.desc)

	def _encrypt_seed(self):
		d = self.ssdata
		d.salt     = sha256(get_random(128)).digest()[:g.salt_len]
		key        = make_key(d.passwd, d.salt, d.hash_preset)
		d.key_id   = make_chksum_8(key)
		d.enc_seed = encrypt_seed(self.seed.data,key)

class Mnemonic (SeedSourceUnenc):

	desc = "mnemonic data"
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

	def _encode(self):

		wl = self._get_wordlist()
		seed_hex = hexlify(self.seed.data)
		mn = self._hextobaseN(self.mn_base,seed_hex,wl,self._hex2mn_pad(seed_hex))

		rev = self._baseNtohex(self.mn_base,mn,wl,self._mn2hex_pad(mn))
		if rev != seed_hex:
			msg("ERROR: seed recomputed from wordlist doesn't match original seed!")
			msg("Original seed:   %s" % seed_hex)
			msg("Recomputed seed: %s" % rev)
			sys.exit(3)

		self.ssdata.mnemonic = mn

	def _format(self):
		self.fmt_data = " ".join(self.ssdata.mnemonic) + "\n"

	def _deformat(self):

		mn = self.fmt_data.split()
		wl = self._get_wordlist()

		if len(mn) not in g.mn_lens:
			die(3,"Invalid mnemonic (%i words).  Allowed numbers of words: %s" %
					(len(mn),", ".join([str(i) for i in g.mn_lens])))

		for n,w in enumerate(mn,1):
			if w not in wl:
				die(3,"Invalid mnemonic: word #%s is not in the wordlist" % n)

		self.ssdata.mnemonic = mn

	def _decode(self):

		mn = self.ssdata.mnemonic
		wl = self._get_wordlist()

		seed_hex = self._baseNtohex(self.mn_base,mn,wl,self._mn2hex_pad(mn))

		rev = self._hextobaseN(self.mn_base,seed_hex,wl,self._hex2mn_pad(seed_hex))
		if rev != mn:
			msg("ERROR: mnemonic recomputed from seed not the same as original")
			die(3,"Recomputed mnemonic:\n%s" % " ".join(rev))

		qmsg("Valid mnemonic for seed ID %s" % make_chksum_8(unhexlify(seed_hex)))

		self.seed = Seed(unhexlify(seed_hex))

	def _filename(self):
		return "%s.%s" % (self.seed.sid, g.mn_ext)

class SeedFile (SeedSourceUnenc):

	desc = "seed data"

	def _encode(self):
		b58seed = b58encode_pad(self.seed.data)
		self.ssdata.chksum = make_chksum_6(b58seed)
		self.ssdata.b58seed = b58seed

	def _decode(self):

		seed = b58decode_pad(self.ssdata.b58seed)
		if seed == False:
			msg("Invalid base 58 string: %s" % val)
			return False

		msg("Valid seed data for seed ID %s" % make_chksum_8(seed))
		self.seed = Seed(seed)

	def _format(self):
		self.fmt_data = "%s %s\n" % (
				self.ssdata.chksum,
				split_into_columns(4,self.ssdata.b58seed)
			)

	def _deformat(self):
		what = self.desc
		ld = self.fmt_data.split()

		if not (7 <= len(ld) <= 12): # 6 <= padded b58 data (ld[1:]) <= 11
			msg("Invalid data length (%s) in %s" % (len(ld),what))
			return False

		a,b = ld[0],"".join(ld[1:])

		if not is_chksum_6(a):
			msg("'%s': invalid checksum format, in %s" % (a, what))
			return False

		if not is_b58string(b):
			msg("'%s': not a base 58 string, in %s" % (b, what))
			return False

		vmsg_r("Validating %s checksum..." % what)

		compare_chksums(a,"checksum",make_chksum_6(b),"base 58 data")

		self.ssdata.chksum = a
		self.ssdata.b58seed = b

	def _filename(self):
		return "%s.%s" % (self.seed.sid, g.seed_ext)

class Wallet (SeedSourceEnc):

	desc = "{pnm} wallet".format(pnm=pnm)

	def _encode(self):
		d = self.ssdata
		d.label = opt.label or "No Label"
		d.pw_status = "NE" if len(d.passwd) else "E"
		d.timestamp = make_timestamp()

	def _format(self):
		d = self.ssdata
		s = self.seed
		s_fmt  = b58encode_pad(d.salt)
		es_fmt = b58encode_pad(d.enc_seed)
		lines = (
			d.label,
			"{} {} {} {} {}".format(s.sid.lower(), d.key_id.lower(),
										s.len_bits, d.pw_status, d.timestamp),
			"{}: {} {} {}".format(d.hash_preset,*get_hash_params(d.hash_preset)),
			"{} {}".format(make_chksum_6(s_fmt),  split_into_columns(4,s_fmt)),
			"{} {}".format(make_chksum_6(es_fmt), split_into_columns(4,es_fmt))
		)
		chksum = make_chksum_6(" ".join(lines))
		self.fmt_data = "%s\n" % "\n".join((chksum,)+lines)

	def _decode(self):
		d = self.ssdata
		# Needed for multiple transactions with {}-txsign
		prompt_add = " "+self.infile.name if opt.quiet else ""
		passwd = get_mmgen_passphrase(self.desc+prompt_add)
		key = make_key(passwd, d.salt, d.hash_preset)
		self.seed = Seed(decrypt_seed(d.enc_seed, key, d.seed_id, d.key_id))
		self.ssdata.passwd = passwd

	def _check_master_chksum(self,lines):

		if len(lines) != 6:
			vmsg("Invalid number of lines (%s) in %s data" % (len(lines),self.desc))
		elif not is_chksum_6(lines[0]):
			vmsg("Incorrect Master checksum (%s) in %s data" % (lines[0],self.desc))
		else:
			chk = make_chksum_6(" ".join(lines[1:]))
			if compare_chksums(lines[0],"master wallet",chk,"computed"):
				return True

		msg("Invalid %s data" % self.desc)
		sys.exit(2)

	def _deformat(self):

		qmsg("Getting {pnm} wallet data from file '{f}'".format(
			pnm=pnm,f=self.infile.name))

		lines = self.fmt_data.rstrip().split("\n")

		self._check_master_chksum(lines)

		d = self.ssdata
		d.label = lines[1]

		d1,d2,d3,d4,d5 = lines[2].split()
		d.seed_id = d1.upper()
		d.key_id  = d2.upper()
		d.seed_len = int(d3)
		d.pw_status,d.timestamp = d4,d5

		hpdata = lines[3].split()
		d.hash_preset = hpdata[0][:-1]  # a string!
		hash_params = [int(i) for i in hpdata[1:]]

		if hash_params != get_hash_params(d.hash_preset):
			msg("Hash parameters '%s' don't match hash preset '%s'" %
					(" ".join(hash_params), d.hash_preset))
			sys.exit(3)

		for i,key in (4,"salt"),(5,"enc_seed"):
			l = lines[i].split(" ",1)
			if len(l) != 2:
				msg("Invalid format for %s in %s: %s" % (key,self.desc,val))
				sys.exit(3)
			chk,val = l[0],l[1].replace(" ","")
			compare_chksums(chk,"wallet "+key,
								make_chksum_6(val),"computed checksum")
			val_bin = b58decode_pad(val)
			if val_bin == False:
				msg("Invalid base 58 number: %s" % val)
				sys.exit(3)
			setattr(d,key,val_bin)

	def _filename(self):
		return "{}-{}[{},{}].{}".format(
				self.seed.sid,
				self.ssdata.key_id,
				self.seed.len_bits,
				self.ssdata.hash_preset,
				g.wallet_ext
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
# 			("Seed length:",   "%s bits (%s bytes)" % (s.len_bits,s.len_bytes)),
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

	desc = "brainwallet"

	def _deformat(self):
		self.brainpasswd = " ".join(self.fmt_data.split())

	def _decode(self):
		self._get_hash_preset()
		vmsg_r("Hashing brainwallet data.  Please wait...")
		# Use buflen arg of scrypt.hash() to get seed of desired length
		seed = scrypt_hash_passphrase(self.brainpasswd, "",
					self.ssdata.hash_preset, buflen=opt.seed_len/8)
		vmsg("Done")
		self.seed = Seed(seed)


class IncogWallet (SeedSourceEnc):

	desc = "incognito wallet"

	_icg_msg = {
		'incog_iv_id': """
Check that the generated Incog ID above is correct.  If it's not, then your
incognito data is incorrect or corrupted.
	""".strip(),
		'incog_iv_id_hidden': """
Check that the generated Incog ID above is correct.  If it's not, then your
incognito data is incorrect or corrupted, or you've supplied an incorrect
offset.
	""".strip(),
	'incorrect_incog_passphrase_try_again': """
Incorrect passphrase, hash preset, or maybe old-format incog wallet.
Try again? (Y)es, (n)o, (m)ore information:
""".strip(),
	'confirm_seed_id': """
If the seed ID above is correct but you're seeing this message, then you need
to exit and re-run the program with the '--old-incog-fmt' option.
""".strip(),
	}

	def _make_iv_chksum(self,s): return sha256(s).hexdigest()[:8].upper()

	def _get_incog_data_len(self,seed_len):
		return g.aesctr_iv_len + g.salt_len + g.hincog_chk_len + seed_len/8

	def _encode (self):
		d = self.ssdata
		# IV is used BOTH to initialize counter and to salt password!
		d.iv = get_random(g.aesctr_iv_len)
		d.iv_id = self._make_iv_chksum(d.iv)
		msg("Incog ID: %s" % d.iv_id)

		d.salt = get_random(g.salt_len)
		key = make_key(d.passwd, d.salt, d.hash_preset, "incog wallet key")
		chk = sha256(self.seed.data).digest()[:8]
		d.enc_seed = encrypt_data(chk + self.seed.data, key, 1, "seed")

		d.wrapper_key = make_key(d.passwd, d.iv, d.hash_preset, "incog wrapper key")
		d.key_id = make_chksum_8(d.wrapper_key)
		d.target_data_len = self._get_incog_data_len(opt.seed_len)

	def _format(self):
		d = self.ssdata
		self.fmt_data = d.iv + encrypt_data(
							d.salt + d.enc_seed,
							d.wrapper_key,
							int(hexlify(d.iv),16),
							"incog data"
						)

	def _filename(self):
		return "{}-{}-{}[{},{}].{}".format(
				self.seed.sid,
				self.ssdata.key_id,
				self.ssdata.iv_id,
				self.seed.len_bits,
				self.ssdata.hash_preset,
				g.incog_ext
			)

	def _deformat(self):

		# Data could be of invalid length, so check: [56, 64, 72]
		valid_dlen = self._get_incog_data_len(opt.seed_len)
		raw_d = self.fmt_data
		if len(raw_d) != valid_dlen:
			msg("Invalid incognito data size: %s" % len(raw_d))
			msg("Valid incognito data size for this seed length: %s bytes" %
					valid_dlen)
			for sl in g.seed_lens:
				if len(raw_d) == self._get_incog_data_len(sl):
					die(1,"Maybe you need to specify a seed length of %s?" % sl)
			die(1,"The data size is invalid for all available seed lengths")

		d = self.ssdata
		d.iv             = raw_d[0:g.aesctr_iv_len]
		d.incog_id       = self._make_iv_chksum(d.iv)
		d.enc_incog_data = raw_d[g.aesctr_iv_len:]
		msg("Incog ID: %s" % d.incog_id)
		qmsg("Check the applicable value against your records")
		ksuf = '_hidden' if self.__class__ == "IncogWalletHidden" else ""
		vmsg("\n%s\n" % self._icg_msg['incog_iv_id' + ksuf])

	def _decode(self):
		d = self.ssdata
		prompt_info="{pnm} incognito wallet".format(pnm=pnm)

		while True:
			passwd = get_mmgen_passphrase(prompt_info+" "+d.incog_id)

			qmsg("Configured hash presets: %s" %
						" ".join(sorted(g.hash_presets)))
			d.hash_preset = get_hash_preset_from_user(what="incog wallet")

			# IV is used BOTH to initialize counter and to salt password!
			key = make_key(passwd, d.iv, d.hash_preset, "wrapper key")
			dd = decrypt_data(d.enc_incog_data, key,
					int(hexlify(d.iv),16), "incog data")

			d.salt     = dd[0:g.salt_len]
			d.enc_seed = dd[g.salt_len:]

			key = make_key(passwd, d.salt, d.hash_preset, "main key")
			vmsg("Key ID: %s" % make_chksum_8(key))

			ret = decrypt_seed(d.enc_seed, key, "", "")

			chk,seed_maybe = ret[:8],ret[8:]
			if sha256(seed_maybe).digest()[:8] == chk:
				msg("Passphrase and hash preset are correct")
				seed = seed_maybe
				break
			else:
				msg("Incorrect passphrase or hash preset")

		self.seed = Seed(seed)


class IncogWalletHex (IncogWallet):

	def _deformat(self):
		self.fmt_data = decode_pretty_hexdump(self.fmt_data)
		IncogWallet._deformat(self)

	def _format(self):
		IncogWallet._format(self)
		self.fmt_data = pretty_hexdump(self.fmt_data)

	def _filename(self):
		return IncogWallet._filename(self)[:-len(g.incog_ext)] + g.incog_hex_ext


class IncogWalletHidden (IncogWallet):

	_hicg_msg = {
		'choose_file_size': """
You must choose a size for your new hidden incog data.  The minimum size is
{} bytes, which puts the incog data right at the end of the file. Since you
probably want to hide your data somewhere in the middle of the file where
it's harder to find, you're advised to choose a much larger file size.
	""".strip(),
	}

	def _get_hincog_params(self):
		a,b = opt.hidden_incog_params.split(",")
		return a,int(b)

	def _check_valid_offset(self,fn,action):
		d = self.ssdata
		if fn.size < d.hincog_offset + d.target_data_len:
			die(1,
"Destination file has length %s, too short to %s %s bytes of data at offset %s"
				% (fn.size,action,d.target_data_len,d.hincog_offset))


	# overrides method in SeedSource
	def _get_formatted_data(self,fn):
		if fn: die(1,
"Specify the filename as a parameter of the '--from-hidden-incog' option")
		d = self.ssdata
		f,d.hincog_offset = self._get_hincog_params()
		self.infile = Filename(f,ftype="hincog")

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
		fn,d.hincog_offset = self._get_hincog_params()

		self.hincog_data_is_new = False
		try:
			os.stat(fn)
		except:
			if keypress_confirm("Requested file '%s' does not exist.  Create?"
					% fn, default_yes=True):
				min_fsize = d.target_data_len + d.hincog_offset
				msg(self._hicg_msg['choose_file_size'].format(min_fsize))
				while True:
					fsize = my_raw_input("Enter file size: ")
					if is_int(fsize) and int(fsize) >= min_fsize: break
					msg("File size must be an integer no less than %s" % min_fsize)

				g.use_urandchars = True
				from mmgen.tool import rand2file
				rand2file(fn, str(fsize))
				self.hincog_data_is_new = True
			else:
				die(1,"Exiting at user request")

		self.outfile = f = Filename(fn,ftype="hincog")

		if opt.debug:
			Msg("Incog data len %s, offset %s" % (d.target_data_len,d.hincog_offset))

		if not self.hincog_data_is_new:
			self._check_valid_offset(f,"write")
			if not opt.quiet: confirm_or_exit("","alter file '%s'" % f.name)

		fh = os.open(f.name,os.O_RDWR)
		os.lseek(fh, int(d.hincog_offset), os.SEEK_SET)
		os.write(fh, self.fmt_data)
		os.close(fh)
		msg("Incog data written to file '%s' at offset %s" % (f.name,d.hincog_offset))

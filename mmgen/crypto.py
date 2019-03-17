#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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
crypto.py:  Cryptographic and related routines for the MMGen suite
"""

from hashlib import sha256

from mmgen.common import *

crmsg = {
	'usr_rand_notice': """
Since we don't fully trust our OS's random number generator, we'll provide
some additional entropy of our own.  Please type {} symbols on your keyboard.
Type slowly and choose your symbols carefully for maximum randomness.  Try to
use both upper and lowercase as well as punctuation and numerals.  What you
type will not be displayed on the screen.  Note that the timings between your
keystrokes will also be used as a source of randomness.
"""
}

def sha256_rounds(s,n):
	assert is_int(n) and n > 0
	for i in range(n):
		s = sha256(s).digest()
	return s

def scramble_seed(seed,scramble_key,hash_rounds):
	import hmac
	scr_seed = hmac.new(seed,scramble_key,sha256).digest()
	fs = 'Seed:  {}\nScramble key: {}\nScrambled seed: {}'
	dmsg(fs.format(seed.hex(),scramble_key.decode(),scr_seed.hex()))
	return sha256_rounds(scr_seed,hash_rounds)

def encrypt_seed(seed,key):
	return encrypt_data(seed,key,iv=1,desc='seed')

def decrypt_seed(enc_seed,key,seed_id,key_id):
	vmsg_r('Checking key...')
	chk1 = make_chksum_8(key)
	if key_id:
		if not compare_chksums(key_id,'key ID',chk1,'computed'):
			msg('Incorrect passphrase or hash preset')
			return False

	dec_seed = decrypt_data(enc_seed,key,iv=1,desc='seed')
	chk2     = make_chksum_8(dec_seed)
	if seed_id:
		if compare_chksums(seed_id,'Seed ID',chk2,'decrypted seed'):
			qmsg('Passphrase is OK')
		else:
			if not opt.debug:
				msg_r('Checking key ID...')
				if compare_chksums(key_id,'key ID',chk1,'computed'):
					msg('Key ID is correct but decryption of seed failed')
				else:
					msg('Incorrect passphrase or hash preset')
			vmsg('')
			return False
#	else:
#		qmsg('Generated IDs (Seed/Key): {}/{}'.format(chk2,chk1))

	dmsg('Decrypted seed: {}'.format(dec_seed.hex()))
	return dec_seed

def encrypt_data(data,key,iv=1,desc='data',verify=True):
	# 192-bit seed is 24 bytes -> not multiple of 16.  Must use MODE_CTR
	from Crypto.Cipher import AES
	from Crypto.Util import Counter
	vmsg('Encrypting {}'.format(desc))
	c = AES.new(key,AES.MODE_CTR,counter=Counter.new(g.aesctr_iv_len*8,initial_value=iv))
	enc_data = c.encrypt(data)

	if verify:
		vmsg_r('Performing a test decryption of the {}...'.format(desc))
		c = AES.new(key,AES.MODE_CTR,counter=Counter.new(g.aesctr_iv_len*8,initial_value=iv))
		dec_data = c.decrypt(enc_data)

		if dec_data == data: vmsg('done')
		else:
			die(2,"ERROR.\nDecrypted {s} doesn't match original {s}".format(s=desc))

	return enc_data

def decrypt_data(enc_data,key,iv=1,desc='data'):
	from Crypto.Cipher import AES
	from Crypto.Util import Counter
	vmsg_r('Decrypting {} with key...'.format(desc))
	c = AES.new(key,AES.MODE_CTR,counter=Counter.new(g.aesctr_iv_len*8,initial_value=iv))
	return c.decrypt(enc_data)

def scrypt_hash_passphrase(passwd,salt,hash_preset,buflen=32):

	# Buflen arg is for brainwallets only, which use this function to generate
	# the seed directly.
	N,r,p = get_hash_params(hash_preset)
	if type(passwd) == str: passwd = passwd.encode()

	try:
		assert not g.use_standalone_scrypt_module
		from hashlib import scrypt # Python >= v3.6
		return scrypt(passwd,salt=salt,n=2**N,r=r,p=p,maxmem=0,dklen=buflen)
	except:
		import scrypt
		return scrypt.hash(passwd,salt,2**N,r,p,buflen=buflen)

def make_key(passwd,salt,hash_preset,desc='encryption key',from_what='passphrase',verbose=False):
	if from_what: desc += ' from '
	if opt.verbose or verbose:
		msg_r('Generating {}{}...'.format(desc,from_what))
	key = scrypt_hash_passphrase(passwd,salt,hash_preset)
	if opt.verbose or verbose: msg('done')
	dmsg('Key: {}'.format(key.hex()))
	return key

def _get_random_data_from_user(uchars):
	m = 'Enter {} random symbols' if opt.quiet else crmsg['usr_rand_notice']
	msg(m.format(uchars))
	prompt = 'You may begin typing.  {} symbols left: '

	import time
	from mmgen.term import get_char_raw,kb_hold_protect
	key_data,time_data = bytes(),[]

	for i in range(uchars):
		key_data += get_char_raw('\r'+prompt.format(uchars-i))
		time_data.append(time.time())

	if opt.quiet: msg_r('\r')
	else: msg_r("\rThank you.  That's enough.{}\n\n".format(' '*18))

	fmt_time_data = list(map('{:.22f}'.format,time_data))
	dmsg('\nUser input:\n{!r}\nKeystroke time values:\n{}\n'.format(key_data,'\n'.join(fmt_time_data)))
	prompt = 'User random data successfully acquired.  Press ENTER to continue'
	prompt_and_get_char(prompt,'',enter_ok=True)

	return key_data+''.join(fmt_time_data).encode()

def get_random(length):
	from Crypto import Random
	os_rand = Random.new().read(length)
	if opt.usr_randchars:
		from_what = 'OS random data'
		if not g.user_entropy:
			g.user_entropy = \
				sha256(_get_random_data_from_user(opt.usr_randchars)).digest()
			from_what += ' plus user-supplied entropy'
		else:
			from_what += ' plus saved user-supplied entropy'
		key = make_key(g.user_entropy,'','2',from_what=from_what,verbose=True)
		return encrypt_data(os_rand,key,desc='random data',verify=False)
	else:
		return os_rand

def get_hash_preset_from_user(hp=g.hash_preset,desc='data'):
	prompt = """Enter hash preset for {},
 or hit ENTER to accept the default value ('{}'): """.format(desc,hp)
	while True:
		ret = my_raw_input(prompt)
		if ret:
			if ret in g.hash_presets.keys():
				return ret
			else:
				m = 'Invalid input.  Valid choices are {}'
				msg(m.format(', '.join(sorted(g.hash_presets.keys()))))
				continue
		else: return hp

_salt_len,_sha256_len,_nonce_len = 32,32,32

def mmgen_encrypt(data,desc='data',hash_preset=''):
	salt  = get_random(_salt_len)
	iv    = get_random(g.aesctr_iv_len)
	nonce = get_random(_nonce_len)
	hp    = hash_preset or (
		opt.hash_preset if 'hash_preset' in opt.set_by_user else get_hash_preset_from_user('3',desc))
	m     = ('user-requested','default')[hp=='3']
	vmsg('Encrypting {}'.format(desc))
	qmsg("Using {} hash preset of '{}'".format(m,hp))
	passwd = get_new_passphrase(desc,{})
	key    = make_key(passwd,salt,hp)
	enc_d  = encrypt_data(sha256(nonce+data).digest()+nonce+data,key,int(iv.hex(),16),desc=desc)
	return salt+iv+enc_d

def mmgen_decrypt(data,desc='data',hash_preset=''):
	vmsg('Preparing to decrypt {}'.format(desc))
	dstart = _salt_len + g.aesctr_iv_len
	salt   = data[:_salt_len]
	iv     = data[_salt_len:dstart]
	enc_d  = data[dstart:]
	hp     = hash_preset or (
		opt.hash_preset if 'hash_preset' in opt.set_by_user else get_hash_preset_from_user('3',desc))
	m  = ('user-requested','default')[hp=='3']
	qmsg("Using {} hash preset of '{}'".format(m,hp))
	passwd = get_mmgen_passphrase(desc)
	key    = make_key(passwd,salt,hp)
	dec_d  = decrypt_data(enc_d,key,int(iv.hex(),16),desc)
	if dec_d[:_sha256_len] == sha256(dec_d[_sha256_len:]).digest():
		vmsg('OK')
		return dec_d[_sha256_len+_nonce_len:]
	else:
		msg('Incorrect passphrase or hash preset')
		return False

def mmgen_decrypt_retry(d,desc='data'):
	while True:
		d_dec = mmgen_decrypt(d,desc)
		if d_dec: return d_dec
		msg('Trying again...')

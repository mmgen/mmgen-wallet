#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
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
keygen: Public key generation initialization code for the MMGen suite
"""

from collections import namedtuple
from .key import PrivKey

keygen_public_data = namedtuple(
	'keygen_public_data', [
		'pubkey',
		'viewkey_bytes',
		'pubkey_type',
		'compressed'])

class keygen_base:

	def __init__(self, cfg):
		if not (self.production_safe or cfg.test_suite):
			from .util import die
			die(2,
				f'Public key generator {type(self).__name__!r} is not safe from timing attacks '
				'and may only be used in a testing environment')

	def gen_data(self, privkey):
		assert isinstance(privkey, PrivKey)
		return keygen_public_data(
			self.to_pubkey(privkey),
			self.to_viewkey(privkey),
			privkey.pubkey_type,
			privkey.compressed)

	def to_viewkey(self, privkey):
		return None

	@classmethod
	def get_clsname(cls, cfg, silent=False):
		return cls.__name__

backend_data = {
	'std': {
		'backends': ('libsecp256k1', 'python-ecdsa'),
		'package': 'secp256k1',
	},
	'monero': {
		'backends': ('nacl', 'ed25519ll-djbec', 'ed25519'),
		'package': 'xmr',
	},
	'zcash_z': {
		'backends': ('nacl',),
		'package': 'zec',
	},
}

def get_backends(pubkey_type):
	return backend_data[pubkey_type]['backends']

def get_pubkey_type_cls(pubkey_type):
	import importlib
	return getattr(
		importlib.import_module(f'mmgen.proto.{backend_data[pubkey_type]["package"]}.keygen'),
		'backend')

def _check_backend(cfg, backend, pubkey_type, desc='keygen backend'):

	from .util import is_int, die

	assert is_int(backend), f'illegal value for {desc} (must be an integer)'

	backends = get_backends(pubkey_type)

	if not (1 <= int(backend) <= len(backends)):
		die(1,
			f'{backend}: {desc} out of range\n' +
			'Configured backends: ' +
			' '.join(f'{n}:{k}' for n, k in enumerate(backends, 1))
		)

	cfg._util.qmsg(f'Using backend {backends[int(backend)-1]!r} for public key generation')

	return True

def check_backend(cfg, proto, backend, addr_type):

	from .addr import MMGenAddrType
	pubkey_type = MMGenAddrType(proto, addr_type or proto.dfl_mmtype).pubkey_type

	return  _check_backend(cfg, backend, pubkey_type, desc='--keygen-backend parameter')

def KeyGenerator(cfg, proto, pubkey_type, backend=None, silent=False):
	"""
	factory function returning a key generator backend for the specified pubkey type
	"""
	assert pubkey_type in proto.pubkey_types, f'{pubkey_type!r}: invalid pubkey type for coin {proto.coin}'

	pubkey_type_cls = get_pubkey_type_cls(pubkey_type)

	backend = backend or cfg.keygen_backend

	if backend:
		_check_backend(cfg, backend, pubkey_type)

	backend_id = backend_data[pubkey_type]['backends'][int(backend) - 1 if backend else 0]

	backend_clsname = getattr(
		pubkey_type_cls,
		backend_id.replace('-', '_')
			).get_clsname(cfg, silent=silent)

	return getattr(pubkey_type_cls, backend_clsname)(cfg)

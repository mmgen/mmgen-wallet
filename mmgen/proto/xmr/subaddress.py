# ~/.local/lib/python3.13/site-packages/monero/wallet.py

from nacl import bindings as nacl

from ...util2 import get_keccak
from ...addr import MoneroIdx

from .addrgen import b58enc

keccak_256 = get_keccak()

add = nacl.crypto_core_ed25519_add
scalarmult_base = nacl.crypto_scalarmult_ed25519_base_noclamp
scalarmult = nacl.crypto_scalarmult_ed25519_noclamp

# src/ringct/rctTypes.h:
H = bytes.fromhex('8b655970153799af2aeadc9ff1add0ea6c7251d54154cfa92c173a0dd39c1f94')

def scalar_reduce(v):
	return nacl.crypto_core_ed25519_scalar_reduce(v.ljust(64, b'\0'))

def get_subaddress(*, proto, master_addr, master_svk, acct_idx, addr_idx):
	"""
	Generate subaddress for given account index and address index
	"""

	if acct_idx == addr_idx == 0:
		return master_addr

	acct_idx = MoneroIdx(acct_idx)
	addr_idx = MoneroIdx(addr_idx)

	master_psk = proto.decode_addr(master_addr).bytes[:32] # => psk + pvk

	hash_in = (
		b'SubAddr\0'
		+ master_svk
		+ acct_idx.to_bytes(4, 'little')
		+ addr_idx.to_bytes(4, 'little'))

	m = keccak_256(hash_in).digest()

	# psk = master_psk + m * B
	psk = add(master_psk, scalarmult_base(scalar_reduce(m)))

	# pvk = master_svk * psk
	pvk = scalarmult(master_svk, psk)

	data = proto.addr_fmt_to_ver_bytes['monero_sub'] + psk + pvk
	return b58enc(data + keccak_256(data).digest()[:4])

#
# Adapted from: https://github.com/ethereum/pyethereum/blob/master/ethereum/utils.py
#

from py_ecc.secp256k1 import privtopub,ecdsa_raw_sign,ecdsa_raw_recover
from .. import rlp
from ..rlp.sedes import Binary

from ....util import get_keccak
keccak_256 = get_keccak()

def sha3_256(bstr):
	return keccak_256(bstr).digest()

import struct
ALL_BYTES = tuple( struct.pack('B', i) for i in range(256) )

# from eth_utils:

# Type ignored for `codecs.decode()` due to lack of mypy support for 'hex' encoding
# https://github.com/python/typeshed/issues/300
from typing import AnyStr,Any,Callable,TypeVar
import codecs
import functools

T = TypeVar("T")
TVal = TypeVar("TVal")
TKey = TypeVar("TKey")

def apply_to_return_value(callback: Callable[..., T]) -> Callable[..., Callable[..., T]]:

    def outer(fn):
        # We would need to type annotate *args and **kwargs but doing so segfaults
        # the PyPy builds. We ignore instead.
        @functools.wraps(fn)
        def inner(*args, **kwargs) -> T:  # type: ignore
            return callback(fn(*args, **kwargs))

        return inner

    return outer

to_list = apply_to_return_value(list)
to_set = apply_to_return_value(set)
to_dict = apply_to_return_value(dict)
to_tuple = apply_to_return_value(tuple)
to_list = apply_to_return_value(list)

def encode_hex_0x(value: AnyStr) -> str:
    if not is_string(value):
        raise TypeError("Value must be an instance of str or unicode")
    binary_hex = codecs.encode(value, "hex")  # type: ignore
    return '0x' + binary_hex.decode("ascii")

def decode_hex(value: str) -> bytes:
    if not isinstance(value,str):
        raise TypeError("Value must be an instance of str")
    return codecs.decode(remove_0x_prefix(value), "hex")  # type: ignore

def is_bytes(value: Any) -> bool:
    return isinstance(value, (bytes,bytearray))

def int_to_big_endian(value: int) -> bytes:
    return value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")

def big_endian_to_int(value: bytes) -> int:
    return int.from_bytes(value, "big")
# end from eth_utils

class Memoize:
	def __init__(self, fn):
		self.fn = fn
		self.memo = {}
	def __call__(self, *args):
		if args not in self.memo:
			self.memo[args] = self.fn(*args)
		return self.memo[args]

TT256 = 2 ** 256

def is_numeric(x): return isinstance(x, int)

def is_string(x): return isinstance(x, bytes)

def to_string(value):
	if isinstance(value, bytes):
		return value
	if isinstance(value, str):
		return bytes(value, 'utf-8')
	if isinstance(value, int):
		return bytes(str(value), 'utf-8')

unicode = str

def encode_int32(v):
	return v.to_bytes(32, byteorder='big')

def str_to_bytes(value):
	if isinstance(value, bytearray):
		value = bytes(value)
	if isinstance(value, bytes):
		return value
	return bytes(value, 'utf-8')

def ascii_chr(n):
	return ALL_BYTES[n]

def encode_hex(n):
	if isinstance(n, str):
		return encode_hex(n.encode('ascii'))
	return encode_hex_0x(n)[2:]

def ecrecover_to_pub(rawhash, v, r, s):
	result = ecdsa_raw_recover(rawhash, (v, r, s))
	if result:
		x, y = result
		pub = encode_int32(x) + encode_int32(y)
	else:
		raise ValueError('Invalid VRS')
	assert len(pub) == 64
	return pub


def ecsign(rawhash, key):
	return ecdsa_raw_sign(rawhash, key)


def mk_contract_address(sender, nonce):
	return sha3(rlp.encode([normalize_address(sender), nonce]))[12:]


def mk_metropolis_contract_address(sender, initcode):
	return sha3(normalize_address(sender) + initcode)[12:]


def sha3(seed):
	return sha3_256(to_string(seed))


assert encode_hex(
	sha3(b'')) == 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'


@Memoize
def privtoaddr(k):
	k = normalize_key(k)
	x, y = privtopub(k)
	return sha3(encode_int32(x) + encode_int32(y))[12:]


def normalize_address(x, allow_blank=False):
	if is_numeric(x):
		return int_to_addr(x)
	if allow_blank and x in {'', b''}:
		return b''
	if len(x) in (42, 50) and x[:2] in {'0x', b'0x'}:
		x = x[2:]
	if len(x) in (40, 48):
		x = decode_hex(x)
	if len(x) == 24:
		assert len(x) == 24 and sha3(x[:20])[:4] == x[-4:]
		x = x[:20]
	if len(x) != 20:
		raise Exception("Invalid address format: %r" % x)
	return x


def normalize_key(key):
	if is_numeric(key):
		o = encode_int32(key)
	elif len(key) == 32:
		o = key
	elif len(key) == 64:
		o = decode_hex(key)
	elif len(key) == 66 and key[:2] == '0x':
		o = decode_hex(key[2:])
	else:
		raise Exception("Invalid key format: %r" % key)
	if o == b'\x00' * 32:
		raise Exception("Zero privkey invalid")
	return o


def int_to_addr(x):
	o = [b''] * 20
	for i in range(20):
		o[19 - i] = ascii_chr(x & 0xff)
		x >>= 8
	return b''.join(o)


def remove_0x_prefix(s):
	return s[2:] if s[:2] in (b'0x', '0x') else s


class Denoms():

	def __init__(self):
		self.wei = 1
		self.babbage = 10 ** 3
		self.ada = 10 ** 3
		self.kwei = 10 ** 6
		self.lovelace = 10 ** 6
		self.mwei = 10 ** 6
		self.shannon = 10 ** 9
		self.gwei = 10 ** 9
		self.szabo = 10 ** 12
		self.finney = 10 ** 15
		self.mether = 10 ** 15
		self.ether = 10 ** 18
		self.turing = 2 ** 256 - 1

address = Binary.fixed_length(20, allow_empty=True)

#
# Adapted from: https://github.com/ethereum/pyethereum/blob/master/ethereum/utils.py
#   only funcs, vars required by vendored rlp module retained
#

import struct, functools
from typing import Any, Callable, TypeVar

ALL_BYTES = tuple(struct.pack('B', i) for i in range(256))

T = TypeVar('T')

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

def is_bytes(value: Any) -> bool:
	return isinstance(value, (bytes,bytearray))

def int_to_big_endian(value: int) -> bytes:
	return value.to_bytes((value.bit_length() + 7) // 8 or 1, 'big')

def big_endian_to_int(value: bytes) -> int:
	return int.from_bytes(value, 'big')

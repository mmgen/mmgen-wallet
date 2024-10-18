import os as overlay_fake_os
from .rpc_orig import *

if overlay_fake_os.getenv('MMGEN_BOGUS_UNSPENT_DATA'):

	class overlay_fake_data:
		rpc_init = rpc_init

	async def rpc_init(*args, **kwargs):
		from .obj import NonNegativeInt
		ret = await overlay_fake_data.rpc_init(*args, **kwargs)
		ret.blockcount = NonNegativeInt(1000000)
		return ret

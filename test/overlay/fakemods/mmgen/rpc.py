from .rpc_orig import *

if os.getenv('MMGEN_BOGUS_UNSPENT_DATA'):

	rpc_init_orig = rpc_init

	async def rpc_init(*args,**kwargs):

		ret = await rpc_init_orig(*args,**kwargs)

		ret.blockcount = 1000000

		return ret

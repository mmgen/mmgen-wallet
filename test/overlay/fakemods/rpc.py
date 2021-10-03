from .rpc_orig import *

if os.getenv('MMGEN_BOGUS_WALLET_DATA'):

	rpc_init_orig = rpc_init

	async def rpc_init(proto,backend=None,daemon=None,ignore_daemon_version=False):

		ret = await rpc_init_orig(
			proto = proto,
			backend = backend,
			daemon = daemon,
			ignore_daemon_version = ignore_daemon_version )

		ret.blockcount = 1000000

		return ret

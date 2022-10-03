async def erigon_sleep(self):
	from ...globalvars import g
	if self.proto.network == 'regtest' and self.rpc.daemon.id == 'erigon':
		import asyncio
		await asyncio.sleep(5)

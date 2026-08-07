async def erigon_sleep(self):
	if self.proto.network == 'regtest' and self.rpc.daemon.id == 'erigon':
		import asyncio
		await asyncio.sleep(5)

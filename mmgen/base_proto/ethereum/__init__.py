async def erigon_sleep(self):
	from ...globalvars import g
	if self.proto.network == 'regtest' and g.daemon_id == 'erigon':
		import asyncio
		await asyncio.sleep(5)

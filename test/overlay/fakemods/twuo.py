import os
from .twuo_orig import *

if os.getenv('MMGEN_BOGUS_WALLET_DATA'):

	async def fake_set_dates(foo,rpc,us):
		for o in us:
			o.date = 1831006505 - int(9.7 * 60 * (o.confs - 1))

	async def fake_get_unspent_rpc(foo):
		from decimal import Decimal
		import json
		from mmgen.util import get_data_from_file
		return json.loads(get_data_from_file(os.getenv('MMGEN_BOGUS_WALLET_DATA')),parse_float=Decimal)

	TwUnspentOutputs.set_dates = fake_set_dates
	TwUnspentOutputs.get_unspent_rpc = fake_get_unspent_rpc

import os
from .twuo_orig import *

if os.getenv('MMGEN_BOGUS_WALLET_DATA'):

	async def fake_get_unspent_rpc(foo):
		from decimal import Decimal
		import json
		from mmgen.fileutil import get_data_from_file
		return json.loads(get_data_from_file(os.getenv('MMGEN_BOGUS_WALLET_DATA')),parse_float=Decimal)

	BitcoinTwUnspentOutputs.get_unspent_rpc = fake_get_unspent_rpc

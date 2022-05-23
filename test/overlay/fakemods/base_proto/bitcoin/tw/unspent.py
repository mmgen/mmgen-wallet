import os
from .unspent_orig import *

if os.getenv('MMGEN_BOGUS_UNSPENT_DATA'):

	async def fake_get_rpc_data(foo):
		from decimal import Decimal
		import json
		from ....fileutil import get_data_from_file
		return json.loads(get_data_from_file(os.getenv('MMGEN_BOGUS_UNSPENT_DATA')),parse_float=Decimal)

	BitcoinTwUnspentOutputs.get_rpc_data = fake_get_rpc_data

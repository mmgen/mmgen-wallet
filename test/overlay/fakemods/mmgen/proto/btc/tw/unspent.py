import os as overlay_fake_os
from .unspent_orig import *

if overlay_fake_os.getenv('MMGEN_BOGUS_UNSPENT_DATA'):

	class overlay_fake_data:

		async def get_rpc_data(foo):
			from decimal import Decimal
			import json
			from ....fileutil import get_data_from_file
			return json.loads(get_data_from_file(
				overlay_fake_os.getenv('MMGEN_BOGUS_UNSPENT_DATA')),parse_float=Decimal)

	BitcoinTwUnspentOutputs.get_rpc_data = overlay_fake_data.get_rpc_data

import os as overlay_fake_os
from .unspent_orig import *

if overlay_fake_os.getenv('MMGEN_BOGUS_UNSPENT_DATA'):

	class overlay_fake_BitcoinTwUnspentOutputs(BitcoinTwUnspentOutputs):

		async def get_rpc_data(self):
			from decimal import Decimal
			import json
			from ....fileutil import get_data_from_file
			return json.loads(get_data_from_file(
				self.cfg,
				overlay_fake_os.getenv('MMGEN_BOGUS_UNSPENT_DATA')
			))

	BitcoinTwUnspentOutputs.get_rpc_data = overlay_fake_BitcoinTwUnspentOutputs.get_rpc_data

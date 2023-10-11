import os as overlay_fake_os
from .new_orig import *

if overlay_fake_os.getenv('MMGEN_BOGUS_UNSPENT_DATA'):

	class overlay_fake_data:

		async def warn_chg_addr_used(_,us):
			from ..util import ymsg
			ymsg('Bogus unspent data: skipping change address is used check')

	New.warn_chg_addr_used = overlay_fake_data.warn_chg_addr_used

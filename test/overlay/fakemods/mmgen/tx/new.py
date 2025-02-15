import os as overlay_fake_os
from .new_orig import *

if overlay_fake_os.getenv('MMGEN_BOGUS_UNSPENT_DATA'):

	class overlay_fake_New(New):

		async def warn_addr_used(self, proto, chg, desc):
			from ..util import ymsg
			ymsg('Bogus unspent data: skipping used change address check')

	New.warn_addr_used = overlay_fake_New.warn_addr_used

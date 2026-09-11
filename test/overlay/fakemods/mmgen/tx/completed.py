from .completed_orig import *

import os as overlay_fake_os

if overlay_fake_os.getenv('MMGEN_TEST_SUITE_LEGACY_TX'):

	class overlay_fake_Completed(Completed):

		def die_on_version_error(self, errmsg):
			ymsg(errmsg)

	Completed.die_on_version_error = overlay_fake_Completed.die_on_version_error
	DummyCompleted.die_on_version_error = overlay_fake_Completed.die_on_version_error

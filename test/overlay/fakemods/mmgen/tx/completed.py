from .completed_orig import *

class overlay_fake_Completed(Completed):

	def die_on_version_error(self, errmsg):
		ymsg(errmsg)

Completed.die_on_version_error = overlay_fake_Completed.die_on_version_error
DummyCompleted.die_on_version_error = overlay_fake_Completed.die_on_version_error

#!/usr/bin/env python3

"""
test.unit_tests_d.__init__: shared data for unit tests for the MMGen suite
"""

import sys,os

from mmgen.globalvars import g
from mmgen.opts import opt

class unit_tests_base:

	def _silence(self):
		if not opt.verbose:
			self.stdout = sys.stdout
			self.stderr = sys.stderr
			sys.stdout = sys.stderr = g.stdout = g.stderr = open(os.devnull,'w')

	def _end_silence(self):
		if not opt.verbose:
			sys.stdout = g.stdout = self.stdout
			sys.stderr = g.stderr = self.stderr

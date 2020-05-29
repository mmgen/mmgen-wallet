#!/usr/bin/env python3
"""
test/unit_tests_d/ut_lockable.py: unit test for the MMGen suite's Lockable class
"""

from mmgen.common import *
from mmgen.exception import *

class unit_test(object):

	def run_test(self,name,ut):

		from mmgen.base_obj import AttrCtrl,Lockable

		qmsg_r('Testing class AttrCtrl...')

		class MyAttrCtrl(AttrCtrl):
			foo = 'fooval'
		ac = MyAttrCtrl()
		ac.lock()

		ac.foo = 'new fooval'
		ac.foo = 'new fooval2'

		class MyAttrCtrlClsCheck(AttrCtrl):
			_use_class_attr = True
			foo = 'fooval'
			bar = None
		acc = MyAttrCtrlClsCheck()
		acc.lock()

		acc.foo = 'new_fooval'
		acc.foo = 'new_fooval2'
		acc.bar = 'bar val'
		acc.bar = 1 # class attribute bar is None, so can be set to any type

		qmsg('OK')
		qmsg_r('Testing class Lockable...')

		class MyLockable(Lockable): # class has no attrs, like UserOpts
			_set_ok = ('foo','baz')
			_reset_ok = ('bar','baz')

		lc = MyLockable()
		lc.foo = None
		lc.bar = 'barval'
		lc.baz = 1
		lc.qux = 1
		lc.lock()

		lc.foo = 'fooval2'
		lc.bar = 'barval2'
		lc.bar = 'barval3'
		lc.baz = 2
		lc.baz = 3

		class MyLockableClsCheck(Lockable): # class has attrs, like GlobalContext
			_use_class_attr = True
			_set_ok = ('foo','baz')
			_reset_ok = ('bar','baz')
			foo = None
			bar = 1
			baz = 3.5
			qux = 'quxval'

		lcc = MyLockableClsCheck()
		lcc.lock()

		lcc.foo = 'fooval2' # class attribute foo is None, so can be set to any type
		lcc.bar = 2
		lcc.bar = 3   # bar is in reset list
		lcc.baz = 3.2
		lcc.baz = 3.1 # baz is in both lists
		qmsg('OK')

		qmsg('Checking error handling:')

		def bad1(): ac.x = 1
		def bad2(): acc.foo = 1
		def bad3(): lc.foo = 'fooval3'
		def bad4(): lc.baz = 'str'
		def bad5(): lcc.bar = 'str'
		def bad6(): lc.qux  = 2
		def bad7(): lcc.qux = 'quxval2'
		def bad8(): lcc.foo = 'fooval3'
		def bad9(): lc.x = 1
		def bad10(): lcc.x = 1

		ut.process_bad_data((
			('attr (1)',           'AttributeError', 'has no attr', bad1 ),
			('attr (2)',           'AttributeError', 'has no attr', bad9 ),
			('attr (3)',           'AttributeError', 'has no attr', bad10 ),
			('attr type (1)',      'AttributeError', 'type',        bad2 ),
			("attr type (2)",      'AttributeError', 'type',        bad4 ),
			("attr type (3)",      'AttributeError', 'type',        bad5 ),
			("attr (can't set)",   'AttributeError', 'read-only',   bad6 ),
			("attr (can't set)",   'AttributeError', 'read-only',   bad7 ),
			("attr (can't reset)", 'AttributeError', 'reset',       bad3 ),
			("attr (can't reset)", 'AttributeError', 'reset',       bad8 ),
		))

		qmsg('OK')
		return True

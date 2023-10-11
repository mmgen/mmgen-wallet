#!/usr/bin/env python3

"""
test.unit_tests_d.ut_lockable: unit test for the MMGen suite's Lockable class
"""

from ..include.common import qmsg,qmsg_r,vmsg

class unit_test:

	def run_test(self,name,ut):

		from mmgen.base_obj import AttrCtrl,Lockable
		from decimal import Decimal

		qmsg_r('Testing class AttrCtrl...')

		class MyAttrCtrl(AttrCtrl):
			_autolock = False
			foo = 'fooval'
		ac = MyAttrCtrl()
		ac._lock()

		ac.foo = 'new fooval'
		ac.foo = 'new fooval2'

		class MyAttrCtrlAutolock(AttrCtrl):
			pass

		aca = MyAttrCtrlAutolock()

		class MyAttrCtrlClsCheck(AttrCtrl):
			_autolock = False
			_use_class_attr = True
			foo = 'fooval'
			bar = None
		acc = MyAttrCtrlClsCheck()
		acc._lock()

		acc.foo = 'new_fooval'
		acc.foo = 'new_fooval2'
		acc.bar = 'bar val'
		acc.bar = 1 # class attribute bar is None, so can be set to any type

		class MyAttrCtrlDflNone(AttrCtrl):
			_default_to_none = True
			foo = 'fooval'
			bar = None

		acdn = MyAttrCtrlDflNone()
		assert acdn.foo == 'fooval', f'{acdn.foo}'
		assert acdn.bar == None, f'{acdn.bar}'
		assert acdn.baz == None, f'{acdn.baz}'

		qmsg('OK')
		qmsg_r('Testing class Lockable...')

		class MyLockable(Lockable): # class without attrs
			_autolock = False
			_set_ok = ('foo','baz','alpha','beta','gamma','delta','epsilon')
			_reset_ok = ('bar','baz')

		lc = MyLockable()
		lc.foo = None
		lc.bar = 'barval'
		lc.baz = 1
		lc.qux = 1

		# are these considered set?
		lc.alpha = 0             # yes
		lc.beta = False          # yes
		lc.gamma = Decimal('0')  # yes
		lc.delta = 0.0           # yes
		lc.epsilon = []          # no

		lc._lock()

		lc.foo = 'fooval2'
		lc.bar = 'barval2'
		lc.bar = 'barval3'
		lc.baz = 2
		lc.baz = 3

		lc.epsilon = [0]

		class MyLockableClsCheck(Lockable): # class with attrs
			_autolock = False
			_use_class_attr = True
			_set_ok = ('foo','baz')
			_reset_ok = ('bar','baz')
			foo = None
			bar = 1
			baz = 3.5
			qux = 'quxval'

		lcc = MyLockableClsCheck()
		lcc._lock()

		lcc.foo = 'fooval2' # class attribute foo is None, so can be set to any type
		lcc.bar = 2
		lcc.bar = 3   # bar is in reset list
		lcc.baz = 3.2
		lcc.baz = 3.1 # baz is in both lists

		qmsg('OK')
		qmsg_r('Testing class Lockable with autolock...')

		class MyLockableAutolock(Lockable):
			def __init__(self):
				self.foo = True

		lca = MyLockableAutolock()
		assert lca._autolock == True
		assert lca._locked == True
		assert lca.foo == True

		class MyLockableAutolockDflNone(Lockable):
			_default_to_none = True
			foo = 0

		lcdn = MyLockableAutolockDflNone()
		assert lcdn.foo == 0
		assert lcdn.bar == None

		class MyLockableBad(Lockable):
			_set_ok = ('foo','bar')
			foo = 1

		qmsg('OK')
		qmsg_r('Checking error handling...')
		vmsg('')

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

		def bad11(): lc.alpha = 0
		def bad12(): lc.beta = False
		def bad13(): lc.gamma = Decimal('0')
		def bad14(): lc.delta = float(0)
		def bad15(): lc.epsilon = [0]

		def bad16(): lca.foo = None
		def bad17(): lb = MyLockableBad()
		def bad18(): aca._lock()

		def bad19(): acdn.baz = None
		def bad20(): lcdn.foo = 1
		def bad21(): lcdn.bar = None
		def bad22(): del lcdn.foo

		ut.process_bad_data((
			('attr (1)',           'AttributeError', 'has no attr', bad1 ),
			('attr (2)',           'AttributeError', 'has no attr', bad9 ),
			('attr (3)',           'AttributeError', 'has no attr', bad10 ),
			('attr (4)',           'AttributeError', 'has no attr', bad19 ),
			('attr (5)',           'AttributeError', 'has no attr', bad21 ),
			('attr type (1)',      'AttributeError', 'type',        bad2 ),
			("attr type (2)",      'AttributeError', 'type',        bad4 ),
			("attr type (3)",      'AttributeError', 'type',        bad5 ),
			("attr (can't set)",   'AttributeError', 'read-only',   bad6 ),
			("attr (can't set)",   'AttributeError', 'read-only',   bad7 ),
			("attr (can't set)",   'AttributeError', 'read-only',   bad20 ),
			("attr (can't reset)", 'AttributeError', 'reset',       bad3 ),
			("attr (can't reset)", 'AttributeError', 'reset',       bad8 ),
			("attr (can't reset)", 'AttributeError', 'reset',       bad11 ),
			("attr (can't reset)", 'AttributeError', 'reset',       bad12 ),
			("attr (can't reset)", 'AttributeError', 'reset',       bad13 ),
			("attr (can't reset)", 'AttributeError', 'reset',       bad14 ),
			("attr (can't reset)", 'AttributeError', 'reset',       bad15 ),
			("attr (can't set)",   'AttributeError', 'read-only',   bad16 ),
			("attr (bad _set_ok)", 'AssertionError', 'not found in',bad17 ),
			("attr (can’t delete)",'AttributeError', 'not be delet',bad22 ),
			("call to _lock()",    'AssertionError', 'only once',   bad18 ),
		))

		qmsg('OK')
		return True

#!/usr/bin/env python3

"""
test.modtest_d.lockable: unit test for the MMGen suite's Lockable class
"""

from decimal import Decimal
from mmgen.base_obj import AttrCtrl, Lockable

class unit_tests:

	def attrctl(self, name, ut, desc='AttrCtrl class'):

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
		assert acdn.bar is None, f'{acdn.bar}'
		assert acdn.baz is None, f'{acdn.baz}'

		def bad1(): ac.x = 1
		def bad2(): acc.foo = 1
		def bad3(): aca._lock()
		def bad4(): acdn.baz = None

		ut.process_bad_data((
			('attr',            'AttributeError', 'has no attr', bad1),
			('attr type',       'AttributeError', 'type',        bad2),
			('call to _lock()', 'AssertionError', 'only once',   bad3),
			('attr',            'AttributeError', 'has no attr', bad4),
		))

		return True

	def base(self, name, ut, desc='Lockable class'):

		class MyLockable(Lockable): # class without attrs
			_autolock = False
			_set_ok = ('foo', 'baz', 'alpha', 'beta', 'gamma', 'delta', 'epsilon')
			_reset_ok = ('bar', 'baz')

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

		def bad1(): lc.foo = 'fooval3'
		def bad2(): lc.baz = 'str'
		def bad3(): lc.qux  = 2
		def bad4(): lc.x = 1
		def bad5(): lc.alpha = 0
		def bad6(): lc.beta = False
		def bad7(): lc.gamma = Decimal('0')
		def bad8(): lc.delta = float(0)
		def bad9(): lc.epsilon = [0]

		ut.process_bad_data((
			('attr (can’t reset)', 'AttributeError', 'reset',       bad1),
			('attr type (2)',      'AttributeError', 'type',        bad2),
			('attr (can’t set)',   'AttributeError', 'read-only',   bad3),
			('attr (2)',           'AttributeError', 'has no attr', bad4),
			('attr (can’t reset)', 'AttributeError', 'reset',       bad5),
			('attr (can’t reset)', 'AttributeError', 'reset',       bad6),
			('attr (can’t reset)', 'AttributeError', 'reset',       bad7),
			('attr (can’t reset)', 'AttributeError', 'reset',       bad8),
			('attr (can’t reset)', 'AttributeError', 'reset',       bad9),
		))

		return True

	def classattr(self, name, ut, desc='Lockable class with class attrs'):

		class MyLockableClsCheck(Lockable): # class with attrs
			_autolock = False
			_use_class_attr = True
			_set_ok = ('foo', 'baz')
			_reset_ok = ('bar', 'baz')
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

		def bad1(): lcc.bar = 'str'
		def bad2(): lcc.qux = 'quxval2'
		def bad3(): lcc.foo = 'fooval3'
		def bad4(): lcc.x = 1

		ut.process_bad_data((
			('attr type (3)',      'AttributeError', 'type',        bad1),
			('attr (can’t set)',   'AttributeError', 'read-only',   bad2),
			('attr (can’t reset)', 'AttributeError', 'reset',       bad3),
			('attr (3)',           'AttributeError', 'has no attr', bad4),
		))

		return True

	def autolock(self, name, ut, desc='Lockable class with autolock'):

		class MyLockableAutolock(Lockable):
			def __init__(self):
				self.foo = True

		lca = MyLockableAutolock()
		assert lca._autolock is True
		assert lca._locked is True
		assert lca.foo is True

		class MyLockableAutolockDflNone(Lockable):
			_default_to_none = True
			foo = 0

		lcdn = MyLockableAutolockDflNone()
		assert lcdn.foo == 0
		assert lcdn.bar is None

		class MyLockableBad(Lockable):
			_set_ok = ('foo', 'bar')
			foo = 1

		def bad1(): lca.foo = None
		def bad2(): MyLockableBad()
		def bad3(): lcdn.foo = 1
		def bad4(): lcdn.bar = None
		def bad5(): del lcdn.foo

		ut.process_bad_data((
			('attr (can’t set)',    'AttributeError', 'read-only',    bad1),
			('attr (bad _set_ok)',  'AssertionError', 'not found in', bad2),
			('attr (can’t set)',    'AttributeError', 'read-only',    bad3),
			('attr (5)',            'AttributeError', 'has no attr',  bad4),
			('attr (can’t delete)', 'AttributeError', 'not be delet', bad5),
		))

		return True

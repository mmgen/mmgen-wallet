#!/usr/bin/env python3

"""
test.modtest_d.indexed_dict: IndexedDict class unit test for the MMGen suite
"""

from mmgen.util import msg, msg_r, die

from ..include.common import vmsg

class unit_test:

	def run_test(self, name, ut):
		bad_msg = (
			'initializing values via constructor',
			'reassignment to existing key',
			'item deletion',
			'item moving',
			'clearing',
			'updating')
		def bad0(): IndexedDict(arg)
		def bad1(): d['a'] = 2
		def bad2(): del d['a']
		def bad3(): d.move_to_end('a')
		def bad4(): d.clear()
		def bad5(): d.update(d)

		def odie(n): die(4, f'\nillegal action {bad_msg[n]!r} failed to raise exception')
		def omsg(e): vmsg(' - ' + e.args[0])

		msg_r('Testing class IndexedDict...')

		from mmgen.obj import IndexedDict
		d = IndexedDict()

		d['a'] = 1
		d['b'] = 2

		vmsg('\nChecking error handling:')

		arg = [('a', 1), ('b', 2)]
		dict(arg)

		for n, func in enumerate([bad0, bad1, bad2, bad3, bad4, bad5]):
			try:
				func()
			except NotImplementedError as e:
				omsg(e)
			else:
				odie(n)

		try:
			d.key(2)
		except Exception as e:
			omsg(e)
		else:
			odie('list index out of range')

		d['c'] = 3

		d_chk = {'a':1, 'b':2, 'c':3}
		assert d == d_chk, d

		d_keys_chk = ['a', 'b', 'c']
		assert d.keys == d_keys_chk, d.keys

		A = d.key(0)
		assert A == 'a', A

		A = d.key(2)
		assert A == 'c', A

		msg('OK')
		return True

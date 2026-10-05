"""
test.modtest_d.algo: algorithm unit tests for the MMGen suite
"""

from ..include.common import vmsg

class unit_tests:

	def get_start(self, name, ut, desc='get_start() bisecting algorithm'):

		from mmgen.algo import get_start

		def gs(data, bot, top, target, bisect_key_func, match_key_func):
			return get_start(
				data            = data,
				bot             = bot,
				top             = top,
				target          = target,
				bisect_key_func = bisect_key_func,
				match_key_func  = match_key_func)

		def bisect_key_func(d):
			return d

		def substr_3(d):
			return d[:3]

		fs = '{:<3} {:<3} {:<6} {:<14}  {:<5} {}'

		data = ('aaaa', 'aaba', 'aabb', 'aaca', 'aada', 'aaea', 'aaeb', 'aaec', 'aafa', 'aaga')
		last = len(data) - 1

		vmsg('\nDATA:\n  {}\n  {}\n'.format(
			'    '.join(str(n) for n in range(len(data))),
			' '.join(data)))

		vmsg(fs.format('BOT', 'TOP', 'TARGET', 'MATCH_KEY_FUNC', 'START', 'START_VAL'))

		for bot, top, target, match_key_func, chk in (
				(0,    0,    'aaa', substr_3, 0),
				(0,    1,    'aaa', substr_3, 0),
				(0,    2,    'aaa', substr_3, 0),
				(0,    last, 'aaa', substr_3, 0),
				(0,    last, 'aag', substr_3, 9),
				(last, last, 'aag', substr_3, 9),
				(7,    last, 'aag', substr_3, 9),
				(8,    last, 'aag', substr_3, 9),
				(0,    last, 'aac', substr_3, 3),
				(2,    3,    'aac', substr_3, 3),
				(0,    3,    'aac', substr_3, 3),
				(3,    3,    'aac', substr_3, 3),
				(3,    4,    'aac', substr_3, 3),
				(2,    4,    'aac', substr_3, 3),
				(2,    5,    'aac', substr_3, 3),
				(1,    3,    'aac', substr_3, 3),
				(3,    5,    'aac', substr_3, 3),
				(3,    last, 'aac', substr_3, 3),
				(4,    4,    'aad', substr_3, 4),
				(4,    4,    'aae', substr_3, None),
				(6,    6,    'aae', substr_3, 6),
				(3,    last, 'aae', substr_3, 5),
				(5,    5,    'aae', substr_3, 5),
				(4,    5,    'aae', substr_3, 5),
				(3,    5,    'aae', substr_3, 5),
				(3,    3,    'aae', substr_3, None),
				(7,    7,    'aae', substr_3, 7),
				(8,    8,    'aae', substr_3, None),
				(8,    last, 'aae', substr_3, None)):

			start = gs(data, bot, top, target, bisect_key_func, match_key_func)

			vmsg(fs.format(
				bot, top, target, match_key_func.__name__,
				'None' if start is None else start,
				'-' if start is None else f'{data[start]}'))

			assert start == chk, f'{start=} != {chk=}'

		vmsg('\nTesting error handling:')

		bad1 = lambda: gs(data, 1, 0,      'aa', bisect_key_func, substr_3)
		bad2 = lambda: gs(data, 1, last+1, 'aa', bisect_key_func, substr_3)

		bad_data = (
			('bot > top',        'AssertionError', '>',  bad1),
			('top >= len(data)', 'AssertionError', '>=', bad2))

		ut.process_bad_data(bad_data, pfx='')

		return True

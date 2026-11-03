"""
test.modtest_d.misc: miscellaneous unit tests for the MMGen suite
"""

import re, time
from collections import namedtuple

from mmgen.color import yellow, blue, brown
from ..include.common import vmsg

class unit_tests:

	def format_elapsed_hr(self, name, ut, desc='function util.format_elapsed_hr()'):
		from mmgen.util2 import format_elapsed_hr

		vectors = (
			# t now               rel_now show_secs  out
			(1, 1,                     False, False, '0 minutes'),
			(1, 1,                     True,  False, 'just now'),
			(0, -2,                    True,  False, 'just now'),
			(0, -62,                   True,  False, '1 minute in the future'),
			(0, -62,                   False, False, '1 minute (negative elapsed)'),
			(0, 7,                     False, False, '0 minutes'),
			(0, 7,                     True,  False, 'just now'),
			(0, 60,                    True,  False, '1 minute ago'),
			(0, 67,                    True,  False, '1 minute ago'),
			(0, 7200,                  True,  False, '2 hours ago'),
			(0, 3600 + 180 + 1,        True,  False, '1 hour 3 minutes ago'),
			(0, 3600*27 + 180 + 7,     True,  False, '1 day 3 hours 3 minutes ago'),
			(0, 3600*24*367 + 180 + 7, True,  False, '367 days 3 minutes ago'),

			(1, 1,                     False,  True, '0 seconds'),
			(1, 1,                     True,   True, 'just now'),
			(0, -2,                    True,   True, '2 seconds in the future'),
			(0, -62,                   True,   True, '1 minute 2 seconds in the future'),
			(0, -62,                   False,  True, '1 minute 2 seconds (negative elapsed)'),
			(0, 7,                     False,  True, '7 seconds'),
			(0, 7,                     True,   True, '7 seconds ago'),
			(0, 60,                    False,  True, '1 minute'),
			(0, 67,                    False,  True, '1 minute 7 seconds'),
			(0, 7200,                  False,  True, '2 hours'),
			(0, 3600 + 180 + 1,        False,  True, '1 hour 3 minutes 1 second'),
			(0, 3600*27 + 180 + 7,     False,  True, '1 day 3 hours 3 minutes 7 seconds'),
			(0, 3600*24*367 + 180 + 7, True,   True, '367 days 3 minutes 7 seconds ago'))

		fs = '    {:7}  {:9}  {:<8}    {}'
		vmsg(brown('  vectors:'))
		vmsg(fs.format('REL_NOW', 'SHOW_SECS', 'ELAPSED', 'OUTPUT'))
		for (t, now, rel_now, show_secs, out_chk) in vectors:
			out = format_elapsed_hr(t, now=now, rel_now=rel_now, show_secs=show_secs)
			assert out == out_chk, f'{out} != {out_chk}'
			vmsg(fs.format(repr(rel_now), repr(show_secs), now-t, out))

		vmsg(brown('  real time:'))
		start = time.time() - 3600 - 127
		ret = format_elapsed_hr(start) # test old default behavior
		vmsg(f'    {3600 - 127:<8}    {ret}')
		ret = format_elapsed_hr(start, show_secs=True)
		vmsg(f'    {3600 - 127:<8}    {ret}')

		return True

	def xmr_subaddress(self, name, ut, desc='generating XMR subaddresses'):
		vectors = [
			['45mLzbVEU5jNEN5qrfvbWMEbBK3LHDdzvgtSxiBgoUs7WYyKatHdzzEM612XpKv3xR52JZq5V7GURSbp5EqpqvQ7UCPrmwU'],
			['82x63Tnxi8xTLkU1WvYm3MTDcFZek6AyN1W6TppMtTnUVuK11GRGtXGJLQKCB5cGU7hukQuoKQsMm1hvnW3mrGxY8JQqVWD'],
			[
				'8AEK8kKkU5ddKr8PL32RgoUW97fDeMFrJNJ3Fh15RWfFUqjodYcd6oAjCdrLrYT3io22vFUkB3FAP7r1hgY39bzEKtHGChq',
				'86JzhV6CUy1bFrLoLJ23Qmgmphz5bsMVubLosp87RRstNxCsderXWvRhEe3s1PWdjv1j6mG9t4hSSQ1JXu1bAZRDSvadW9m',
				'88jM6aonkzqP3EcHYCQnMSAHrvv3ZBZo8gC1sVEc4nUgBZsPww3WEx6jfsdLxbWBLE3zVDvp1w6CWAPeybrSF1Cx3BH3EYC',
			]
		]
		from mmgen.proto.xmr.subaddress import get_subaddress
		from mmgen.addrlist import KeyAddrList
		from mmgen.cfg import Config
		from mmgen.protocol import init_proto
		from mmgen.seed import Seed
		with open('test/ref/FE3C6545.hex') as fh:
			seed_hex = fh.read().strip()
		cfg = Config()
		proto = init_proto(cfg, 'xmr', network='regtest')
		kal = KeyAddrList(
			cfg         = cfg,
			proto       = proto,
			seed        = Seed(cfg, seed_bin=bytes.fromhex(seed_hex)),
			addr_idxs   = '4',
			mmtype      = 'M',
			skip_chksum = True)
		data = kal.data[0]
		for acct_idx, addr_idx in (
				(0, 0),
				(1, 0),
				(2, 0),
				(2, 1),
				(2, 2)):
			addr = get_subaddress(
				proto = proto,
				master_addr = data.addr,
				master_svk = bytes.fromhex(data.viewkey),
				acct_idx = acct_idx,
				addr_idx = addr_idx)
			vmsg(f'{acct_idx=} {addr_idx=} {addr=}')
			assert addr == vectors[acct_idx][addr_idx]
		return True

	def xmrwallet_uarg_info(self, name, ut, desc='dict xmrwallet.xmrwallet_uarg_info'): # WIP
		from mmgen.xmrwallet import uarg_info
		vs = namedtuple('vector_data', ['text', 'groups'])
		fs = '{:16} {}'

		vmsg(blue('  ' + fs.format('ID', 'ANNOT')))
		for k, v in uarg_info.items():
			vmsg('  ' + fs.format(k, v[0]))

		vectors = {
			'sweep_spec': (
				vs('1:2',     "('1', '2', None, None)"),
				vs('1:2,3',   "('1', '2', '3', None)"),
				vs('1:2,3:4', "('1', '2', '3', '4')"))}

		vmsg('')
		for k, v in uarg_info.items():
			vmsg(f'  {k}')
			if k in vectors:
				vmsg(f'    pat: {v.pat}')
				vmsg( '    vectors:')
				for vec in vectors[k]:
					m = re.match(v.pat, vec.text)
					vmsg(f'      {vec.text:10} ==> {m.groups()}')
					assert str(m.groups()) == vec.groups
			else:
				vmsg(yellow('    TBD'))

		return True

	def pyversion(self, name, ut, desc='class pyversion.PythonVersion'):
		from mmgen.pyversion import PythonVersion, python_version

		ver = {}
		fs = '{:<7} {:<9} {:<5} {}'
		vmsg('\n' + fs.format('Version', 'PyVersion', 'Major', 'Minor'))

		for k in ('current', '3.3', '3.12', '4.3', '7.0'):
			obj = python_version if k == 'current' else PythonVersion(k)
			major, minor = [int(s) for s in obj.split('.')]
			assert obj.major == major and obj.minor == minor
			vmsg(fs.format(k.upper(), obj, major, minor))
			ver[k] = obj

		vmsg('\nPerforming comparison tests:')

		assert ver['3.3'] == '3.3'

		assert ver['current'] < ver['7.0']
		assert ver['3.3']     < ver['4.3']
		assert ver['3.12']    < ver['7.0']
		assert ver['3.3']     < ver['3.12']

		assert ver['current'] < '7.0'
		assert ver['3.3']     < '4.3'
		assert ver['3.12']    < '7.0'
		assert ver['3.3']     < '3.12' # ensure we’re comparing numerically, not stringwise

		assert ver['current'] <= ver['current']
		assert ver['3.3']     <= '4.3'
		assert ver['3.12']    <= '7.0'
		assert ver['3.3']     <= '3.12'

		assert ver['current'] == ver['current']
		assert ver['3.3']     == ver['3.3']
		assert ver['3.3']     != ver['3.12']
		assert ver['3.3']     != ver['4.3']
		assert ver['3.3']     == '3.3'
		assert ver['3.3']     != '3.12'
		assert ver['3.3']     != '4.3'

		assert ver['current'] > '3.6'
		assert ver['7.0']     > ver['current']
		assert ver['4.3']     > '3.3'
		assert ver['3.12']    > '3.3'

		assert ver['current'] >= ver['current']
		assert ver['7.0']     >= ver['current']
		assert ver['4.3']     >= '3.3'
		assert ver['3.12']    >= '3.12'
		assert ver['3.12']    >= '3.3'

		assert '3.0' < ver['3.12'] < '3.13'
		assert '3.9' < ver['3.12'] # ensure we’re reverse comparing numerically, not stringwise
		assert '3.3' < ver['4.3']  <= '4.3'
		assert '4.3' <= ver['4.3'] <= '4.3'
		assert '4.3' == ver['4.3'] == '4.3'

		return True

	def exp_int(self, name, ut, desc='ExpInt() class'):
		from mmgen.util2 import ExpInt

		for num, trunc, chk, out in (
				('0e0',              0,                  0,                  '0'),
				('0e1',              0,                  0,                  '0'),
				('3e0',              3,                  3,                  '3'),
				('3e1',              30,                 30,                 '30'),
				('3e2',              300,                300,                '300'),
				('3e3',              3000,               3000,               '3e3'),
				(3000,               3000,               3000,               '3e3'),
				(1,                  1,                  1,                  '1'),
				('123e0',            123,                123,                '123'),
				(123,                123,                123,                '123'),
				(12345,              12340,              12345,              '12345'),
				(123456,             123400,             123456,             '123456'),
				(1234567,            1234000,            1234000,            '1234e3'),
				(123456789,          123400000,          123400000,          '1234e5'),
				(998877665544332211, 998800000000000000, 998800000000000000, '9988e14'),
			):
			e = ExpInt(num, prec=4)
			enc = e.enc
			assert enc == out, f'{enc} != {out}'
			assert e.trunc == trunc, f'{e.trunc} != {trunc}'
			vmsg('')
			vmsg(f'num        {num}')
			vmsg(f'enc        {enc}')
			dec = ExpInt(enc, prec=4)
			vmsg(f'enc -> dec {dec}')
			vmsg(f'chk        {chk}')
			assert dec == chk, f'{dec} != {chk}'
			dec_enc = dec.enc
			vmsg(f'dec -> enc {dec_enc}')
			vmsg(f'out        {out}')
			assert dec_enc == out, f'{dec_enc} != {out}'

		return True

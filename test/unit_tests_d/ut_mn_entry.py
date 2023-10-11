#!/usr/bin/env python3

"""
test.unit_tests_d.ut_mn_entry: Mnemonic user entry unit test for the MMGen suite
"""

from mmgen.util import msg,msg_r
from ..include.common import cfg,qmsg

class unit_test:

	vectors = {
		'mmgen':   {
			'usl': 10, 'sw': 3, 'lw': 12,
			'idx_minimal': ( # None: non-unique match. False: no match
				('a',         None),
				('aa',        False),
				('as',        None),
				('ask',       70),
				('afte',      None),
				('after',     None),
				('aftern',    20),
				('afternoon', 20),
				('afternoons',False),
				('g',         None),
				('gg',        False),
				('z',         False),
				('abi',       False),
				('abo',       None),
				('abl',       0),
				('able',      0),
				('abler',     False),
				('you',       None),
				('yout',      1625),
				('youth',     1625),
				('youths',    False),
			),
		},
		'xmrseed': { 'usl': 3, 'sw': 4, 'lw': 12 },
		'bip39':   { 'usl': 4, 'sw': 3, 'lw': 8 },
	}

	def run_test(self,name,ut):

		msg_r('Testing MnemonicEntry methods...')

		from mmgen.mn_entry import mn_entry

		msg_r('\nTesting computed wordlist constants...')
		for wl_id in self.vectors:
			for j,k in (('uniq_ss_len','usl'),('shortest_word','sw'),('longest_word','lw')):
				a = getattr(mn_entry( cfg, wl_id ),j)
				b = self.vectors[wl_id][k]
				assert a == b, f'{wl_id}:{j} {a} != {b}'
		msg('OK')

		msg_r('Testing idx()...')
		qmsg('')
		junk = 'a g z aa gg zz aaa ggg zzz aaaa gggg zzzz aaaaaaaaaaaaaa gggggggggggggg zzzzzzzzzzzzzz'
		for wl_id in self.vectors:
			m = mn_entry( cfg, wl_id )
			qmsg('Wordlist: '+wl_id)
			for entry_mode in ('full','short'):
				for a,word in enumerate(m.wl):
					b = m.idx(word,entry_mode)
					assert a == b, f'{a} != {b} ({word!r} - entry mode: {entry_mode!r})'
				a = None
				for word in junk.split():
					b = m.idx(word,entry_mode)
					assert a == b, f'{a} != {b} ({word!r} - entry mode: {entry_mode!r})'
			if 'idx_minimal' in self.vectors[wl_id]:
				for vec in self.vectors[wl_id]['idx_minimal']:
					chk = vec[1]
					b = m.idx(vec[0],'minimal')
					if chk is False:
						assert b is None, (b,None)
					elif chk is None:
						assert type(b) is tuple, (type(b),tuple)
					elif type(chk) is int:
						assert b == chk, (b,chk)
		msg('OK')

		return True

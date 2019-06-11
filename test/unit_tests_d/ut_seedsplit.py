#!/usr/bin/env python3
"""
test/unit_tests_d/ut_seedsplit: seed splitting unit test for the MMGen suite
"""

from mmgen.common import *

class unit_test(object):

	def run_test(self,name):
		from mmgen.seed import Seed
		from mmgen.obj import SeedShareIdx

		def basic_ops():
			test_data = {
				'default': (
					(8,'4710FBF0','B3D9411B','2670E83D','D1FC57ED','AE49CABE','63FFBA62',256),
					(6,'9D07ABBD','AF5DC2F6','1A3BBDAC','2548AEE9','B94F7450','1F4E5A12',192),
					(4,'43670520','1F72C066','E5AA8DA1','A33966A0','D2BCE0A5','A568C315',128),
				),
				'φυβαρ': (
					(8,'4710FBF0','269D658C','9D25889E','6D730ECB','C61A963F','9FE99C05',256),
					(6,'9D07ABBD','4998B33E','F00CE041','C612BEE5','35CD3675','41B3BE61',192),
					(4,'43670520','77140076','EA82CB30','80F7AEDE','D168D768','77BE57AA',128),
				)
			}

			for id_str in (None,'default','φυβαρ'):
				msg_r('Testing basic ops (id_str={!r})...'.format(id_str))
				vmsg('')

				for a,b,c,d,e,f,h,i in test_data[id_str if id_str is not None else 'default']:
					seed_bin = bytes.fromhex('deadbeef' * a)
					seed = Seed(seed_bin)
					assert seed.sid == b, seed.sid

					for share_count,j,k,l in ((2,c,c,d),(5,e,f,h)):

						shares = seed.split(share_count,id_str)
						A = len(shares)
						assert A == share_count, A

						s = shares.format()
						vmsg_r('\n{}'.format(s))
						assert len(s.strip().split('\n')) == share_count+6, s

						A = shares.get_share_by_idx(1).sid
						B = shares.get_share_by_seed_id(j).sid
						assert A == B == j, A

						A = shares.get_share_by_idx(share_count-1).sid
						B = shares.get_share_by_seed_id(k).sid
						assert A == B == k, A

						A = shares.get_share_by_idx(share_count).sid
						B = shares.get_share_by_seed_id(l).sid
						assert A == B == l, A

						A = shares.join().sid
						assert A == b, A

				msg('OK')

		def defaults_and_limits():
			msg_r('Testing defaults and limits...')

			seed_bin = bytes.fromhex('deadbeef' * 8)
			seed = Seed(seed_bin)

			shares = seed.split(SeedShareIdx.max_val)
			s = shares.format()
#			vmsg_r('\n{}'.format(s))
			assert len(s.strip().split('\n')) == 1030, s

			A = shares.get_share_by_idx(1024).sid
			B = shares.get_share_by_seed_id('4BA23728').sid
			assert A == '4BA23728', A
			assert B == '4BA23728', B

			A = shares.join().sid
			B = seed.sid
			assert A == B, A

			msg('OK')

		def collisions():
			ss_count,last_sid,collisions_chk = (65535,'B5CBCE0A',3)

			msg_r('Testing Seed ID collisions ({} seed shares)...'.format(ss_count))
			vmsg('')

			seed_bin = bytes.fromhex('1dabcdef' * 4)
			seed = Seed(seed_bin)

			SeedShareIdx.max_val = ss_count
			shares = seed.split(ss_count)
			A = shares.get_share_by_idx(ss_count).sid
			B = shares.get_share_by_seed_id(last_sid).sid
			assert A == last_sid, A
			assert B == last_sid, B

			assert shares.nonce_start == 0, shares.nonce_start

			collisions = 0
			for sid in shares.data['long']:
				collisions += shares.data['long'][sid][1]

			assert collisions == collisions_chk, collisions
			vmsg_r('\n{} collisions, last_sid {}'.format(collisions,last_sid))
			msg('OK')

		basic_ops()
		defaults_and_limits()
		collisions()

		return True

#!/usr/bin/env python3
"""
test/unit_tests_d/ut_seedsplit: seed splitting unit test for the MMGen suite
"""

from mmgen.common import *

class unit_test(object):

	def run_test(self,name):
		from mmgen.seed import Seed
		from mmgen.obj import SeedShareIdx

		def basic_ops(master_idx):
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
			test_data_master = {
				'1': {
					'default': (
						(8,'4710FBF0','B512A312','3588E156','9374255D','3E87A907','752A2E4E',256),
						(4,'43670520','05880E2B','C6B438D4','5FF9B5DF','778E9C60','2C01F046',128) ),
					'φυβαρ': (
						(8,'4710FBF0','5FA963B0','69A1F56A','25789CC4','9777A750','E17B9B8B',256),
						(4,'43670520','AF8BFDF8','66F319BE','A5E40978','927549D2','93B2418B',128),
					)
				},
				'5': {
					'default': (
						(8,'4710FBF0','A8A34BC0','F69B6CF8','234B5DCD','BB004DC5','08DC9776',256),
						(4,'43670520','C887A2D6','86AE9445','3188AD3D','07339882','BE3FE72A',128) ),

					'φυβαρ': (
						(8,'4710FBF0','89C35D99','B1CD5854','8414652C','32C24668','17CA1E19',256),
						(4,'43670520','06929789','32E8E375','C6AC3C9D','4BEA2AB2','15AFC7F2',128)
					)
				}
			}
			if master_idx:
				test_data = test_data_master[str(master_idx)]

			for id_str in (None,'default','φυβαρ'):
				msg_r('Testing basic ops (id_str={!r}, master_idx={})...'.format(id_str,master_idx))
				vmsg('')

				for a,b,c,d,e,f,h,i in test_data[id_str if id_str is not None else 'default']:
					seed_bin = bytes.fromhex('deadbeef' * a)
					seed = Seed(seed_bin)
					assert seed.sid == b, seed.sid

					for share_count,j,k,l in ((2,c,c,d),(5,e,f,h)):

						shares = seed.split(share_count,id_str,master_idx)
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

						if master_idx:
							slist = [shares.get_share_by_idx(i+1) for i in range(1,len(shares))]
							A = Seed.join_shares([shares.master_share]+slist,True,master_idx,id_str).sid
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

		basic_ops(master_idx=None)
		basic_ops(master_idx=1)
		basic_ops(master_idx=5)
		defaults_and_limits()
		collisions()

		return True

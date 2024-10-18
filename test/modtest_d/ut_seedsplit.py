#!/usr/bin/env python3

"""
test.modtest_d.ut_seedsplit: seed splitting unit test for the MMGen suite
"""

from mmgen.util import msg, msg_r

from ..include.common import cfg, vmsg, vmsg_r

class unit_test:

	def run_test(self, name, ut):
		from mmgen.seed import Seed
		from mmgen.seedsplit import SeedShareList, SeedShareIdx

		cfg.debug_subseed = bool(cfg.verbose)

		def basic_ops(master_idx):
			test_data = {
				'default': (
					(8, '4710FBF0', 'B3D9411B', '2670E83D', 'D1FC57ED', 'AE49CABE', '63FFBA62', 0, 0),
					(6, '9D07ABBD', 'AF5DC2F6', '1A3BBDAC', '2548AEE9', 'B94F7450', '1F4E5A12', 0, 0),
					(4, '43670520', '1F72C066', 'E5AA8DA1', 'A33966A0', 'D2BCE0A5', 'A568C315', 0, 0),
				),
				'φυβαρ': (
					(8, '4710FBF0', '269D658C', '9D25889E', '6D730ECB', 'C61A963F', '9FE99C05', 0, 0),
					(6, '9D07ABBD', '4998B33E', 'F00CE041', 'C612BEE5', '35CD3675', '41B3BE61', 0, 0),
					(4, '43670520', '77140076', 'EA82CB30', '80F7AEDE', 'D168D768', '77BE57AA', 0, 0),
				)
			}
			test_data_master = {
				'1': {
					'default': (
						(8, '4710FBF0', '6AE6177F', 'AC12090C', '6AE6177F',
							'3E87A907', '7D1FEA56', 'BFEBFFFF', '629A9808'),
						(4, '43670520', '6739535C', 'ABF4DD38', '6739535C',
							'778E9C60', '89CBCFD2', '689FABF5', '70BED76B'),
					),
					'φυβαρ': (
						(8, '4710FBF0', '6AE6177F', 'AC5FA32E', '6AE6177F',
							'9777A750', 'C7CF2AFC', '035AAACB', 'C777FBE4'),
						(4, '43670520', '6739535C', '37EBA2F5', '6739535C',
							'927549D2', '29BADEE7', '9CA73A03', '313F5528'))
				},
				'5': {
					'default': (
						(8, '4710FBF0', '5EFAC3D6', 'B489167D', '5EFAC3D6',
							'BB004DC5', '1A0381C0', '4EA182E3', '547FB2DC'),
						(4, '43670520', 'EE93DB0E', '44962A7D', 'EE93DB0E',
							'07339882', '376A05B1', 'CE51D022', '00149CA3'),
					),
					'φυβαρ': (
						(8, '4710FBF0', '5EFAC3D6', 'A6E27EE3', '5EFAC3D6',
							'32C24668', 'B4C54297', '1EC9B71B', '8C5C6B1C'),
						(4, '43670520', 'EE93DB0E', 'B584E963', 'EE93DB0E',
							'4BEA2AB2', '4BEA65C7', '140FC43F', 'BBD19461'))
				}
			}
			if master_idx:
				test_data = test_data_master[str(master_idx)]

			for id_str in (None, 'default', 'φυβαρ'):
				msg_r(f'Testing basic ops (id_str={id_str!r}, master_idx={master_idx})...')
				vmsg('')

				for a, b, c, d, e, f, h, i, p in test_data[id_str if id_str is not None else 'default']:
					seed_bin = bytes.fromhex('deadbeef' * a)
					seed = Seed(cfg, seed_bin)
					assert seed.sid == b, seed.sid

					for share_count, j, k, l, m in (
							(2, c, c, d, i),
							(5, e, f, h, p)):

						shares = seed.split(share_count, id_str, master_idx)
						A = len(shares)
						assert A == share_count, A

						s = shares.format()
						vmsg_r(f'\n{s}')
						assert len(s.strip().split('\n')) == share_count+6, s

						if master_idx:
							A = shares.get_share_by_idx(1, base_seed=False).sid
							B = shares.get_share_by_seed_id(j, base_seed=False).sid
							assert A == B == m, A

						A = shares.get_share_by_idx(1, base_seed=True).sid
						B = shares.get_share_by_seed_id(j, base_seed=True).sid
						assert A == B == j, A

						A = shares.get_share_by_idx(share_count-1, base_seed=True).sid
						B = shares.get_share_by_seed_id(k, base_seed=True).sid
						assert A == B == k, A

						A = shares.get_share_by_idx(share_count).sid
						B = shares.get_share_by_seed_id(l).sid
						assert A == B == l, A

						A = shares.join().sid
						assert A == b, A

						if master_idx:
							slist = [shares.get_share_by_idx(i+1, base_seed=True) for i in range(len(shares))]
							A = Seed.join_shares(cfg, slist, master_idx, id_str).sid
							assert A == b, A

				msg('OK')

		def defaults_and_limits():
			msg_r('Testing defaults and limits...')

			seed_bin = bytes.fromhex('deadbeef' * 8)
			seed = Seed(cfg, seed_bin)

			shares = seed.split(SeedShareIdx.max_val)
			s = shares.format()
#			vmsg_r(f'\n{s}')
			assert len(s.strip().split('\n')) == 1030, s

			A = shares.get_share_by_idx(1024).sid
			B = shares.get_share_by_seed_id('4BA23728').sid
			assert A == '4BA23728', A
			assert B == '4BA23728', B

			A = shares.join().sid
			B = seed.sid
			assert A == B, A

			msg('OK')

		def collisions(seed_hex, ss_count, last_sid, collisions_chk, master_idx):

			msg_r(f'Testing Seed ID collisions ({ss_count} seed shares, master_idx={master_idx})...')
			vmsg('')

			seed_bin = bytes.fromhex(seed_hex)
			seed = Seed(cfg, seed_bin)

			SeedShareIdx.max_val = ss_count
			shares = seed.split(ss_count, master_idx=master_idx)
			A = shares.get_share_by_idx(ss_count).sid
			B = shares.get_share_by_seed_id(last_sid).sid
			assert A == last_sid, A
			assert B == last_sid, B

			assert shares.nonce_start == 0, shares.nonce_start

			collisions = 0
			for sid in shares.data['long']:
				collisions += shares.data['long'][sid][1]

			assert collisions == collisions_chk, collisions
			vmsg_r(f'{collisions} collisions, last_sid {last_sid}')
			msg('OK')

		def last_share_collisions():
			msg_r('Testing last share collisions with shortened Seed IDs')
			vmsg('')
			seed_bin = bytes.fromhex('2eadbeef'*8)
			seed = Seed(cfg, seed_bin)
			ssm_save = SeedShareIdx.max_val
			ssm = SeedShareIdx.max_val = 2048
			shares = SeedShareList(seed, count=ssm, id_str='foo', master_idx=1, debug_last_share=True)
			lsid = shares.last_share.sid
			collisions = shares.data['long'][lsid][1]
			assert collisions == 2, collisions
			assert lsid == 'B5B8AD09', lsid
			SeedShareIdx.max_val = ssm_save
			vmsg_r(f'{collisions} collisions, last_share sid {lsid}')
			msg('..OK')

		basic_ops(master_idx=None)
		basic_ops(master_idx=1)
		basic_ops(master_idx=5)
		defaults_and_limits()
		last_share_collisions()
		collisions('1dabcdef'*4, 65535, 'B5CBCE0A', 3, master_idx=None)
		collisions('18abcdef'*4, 65535, 'FF03CE82', 3, master_idx=1)

		return True

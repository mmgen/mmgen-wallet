#!/usr/bin/env python3
"""
test.unit_tests_d.ut_rpc: RPC unit test for the MMGen suite
"""

from mmgen.common import *
from mmgen.exception import *

from mmgen.protocol import init_proto
from mmgen.rpc import rpc_init,MoneroWalletRPCClient
from mmgen.daemon import CoinDaemon,MoneroWalletDaemon

def cfg_file_auth_test(proto,d):
	qmsg(cyan(f'\n  Testing authentication with credentials from {d.cfg_file}:'))
	d.remove_datadir() # removes cookie file to force authentication from cfg file
	os.makedirs(d.network_datadir)

	cf = os.path.join(d.datadir,d.cfg_file)
	open(cf,'a').write('\nrpcuser = ut_rpc\nrpcpassword = ut_rpc_passw0rd\n')

	d.flag.keep_cfg_file = True
	d.start()

	async def do():
		rpc = await rpc_init(proto)
		assert rpc.auth.user == 'ut_rpc', f'{rpc.auth.user}: user is not ut_rpc!'

	run_session(do())
	d.stop()

def do_msg(rpc):
	qmsg('  Testing backend {!r}'.format( type(rpc.backend).__name__ ))

class init_test:

	async def btc(proto,backend,daemon):
		rpc = await rpc_init(proto,backend,daemon)
		do_msg(rpc)

		bh = (await rpc.call('getblockchaininfo',timeout=300))['bestblockhash']
		await rpc.gathered_call('getblock',((bh,),(bh,1)),timeout=300)
		await rpc.gathered_call(None,(('getblock',(bh,)),('getblock',(bh,1))),timeout=300)

	async def bch(proto,backend,daemon):
		rpc = await rpc_init(proto,backend,daemon)
		do_msg(rpc)

	ltc = bch

	async def eth(proto,backend,daemon):
		rpc = await rpc_init(proto,backend,daemon)
		do_msg(rpc)
		await rpc.call('eth_blockNumber',timeout=300)

	etc = eth

def run_test(network_ids,test_cf_auth=False,daemon_ids=None):

	def do(d):

		if not opt.no_daemon_stop:
			d.stop()

		if not opt.no_daemon_autostart:
			d.remove_datadir()
			d.start()

		for backend in g.autoset_opts['rpc_backend'].choices:
			test = getattr(init_test,d.proto.coin.lower())
			run_session(test(d.proto,backend,d),backend=backend)

		if not opt.no_daemon_stop:
			d.stop()

		if test_cf_auth and g.platform != 'win':
			cfg_file_auth_test(d.proto,d)

		qmsg('')

	for network_id in network_ids:
		proto = init_proto(network_id=network_id)
		ids = (lambda x:
			set(daemon_ids) & set(x) if daemon_ids else x
			)(CoinDaemon.coins[proto.coin].daemon_ids)
		for daemon_id in ids:
			do( CoinDaemon(proto=proto,test_suite=True,daemon_id=daemon_id) )

	return True

class unit_tests:

	altcoin_deps = ('ltc','bch','geth','erigon','openethereum','parity','xmrwallet')
	win_skip = ('xmrwallet',) # FIXME - wallet doesn't open
	arm_skip = ('openethereum','parity') # no prebuilt binaries for ARM

	def btc(self,name,ut):
		return run_test(['btc','btc_tn'],test_cf_auth=True)

	def ltc(self,name,ut):
		return run_test(['ltc','ltc_tn'],test_cf_auth=True)

	def bch(self,name,ut):
		return run_test(['bch','bch_tn'],test_cf_auth=True)

	def geth(self,name,ut):
		return run_test(['eth_tn','eth_rt'],daemon_ids=['geth']) # mainnet returns EIP-155 error on empty blockchain

	def erigon(self,name,ut):
		return run_test(['eth','eth_tn','eth_rt'],daemon_ids=['erigon'])

	def openethereum(self,name,ut):
		return run_test(['eth','eth_tn','eth_rt'],daemon_ids=['openethereum'])

	def parity(self,name,ut):
		return run_test(['etc'])

	def xmrwallet(self,name,ut):

		async def run():
			networks = init_proto('xmr').networks
			daemons = [(
					CoinDaemon(proto=proto,test_suite=True),
					MoneroWalletDaemon(
						proto      = proto,
						test_suite = True,
						wallet_dir = 'test/trash2',
						passwd     = 'ut_rpc_passw0rd' )
				) for proto in (init_proto('xmr',network=network) for network in networks) ]

			for md,wd in daemons:
				if not opt.no_daemon_autostart:
					md.start()
				wd.start()
				c = MoneroWalletRPCClient(daemon=wd)
				fn = f'monero-{wd.network}-junk-wallet'
				qmsg(f'Creating {wd.network} wallet')
				await c.call(
					'restore_deterministic_wallet',
					filename = fn,
					password = 'foo',
					seed     = baseconv.fromhex('beadface'*8,'xmrseed',tostr=True) )
				qmsg(f'Opening {wd.network} wallet')
				await c.call( 'open_wallet', filename=fn, password='foo' )

			for md,wd in daemons:
				wd.wait = False
				await wd.rpc.stop_daemon()
				if not opt.no_daemon_stop:
					md.wait = False
					await md.rpc.stop_daemon()

			gmsg('OK')

		from mmgen.baseconv import baseconv
		import shutil
		shutil.rmtree('test/trash2',ignore_errors=True)
		os.makedirs('test/trash2')
		run_session(run())
		return True

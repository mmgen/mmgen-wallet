#!/usr/bin/env python3
"""
test.unit_tests_d.ut_rpc: RPC unit test for the MMGen suite
"""

from mmgen.common import *
from mmgen.exception import *

from mmgen.protocol import init_proto
from mmgen.rpc import rpc_init,MoneroWalletRPCClient
from mmgen.daemon import CoinDaemon,MoneroWalletDaemon

def auth_test(proto,d):
	if g.platform != 'win':
		qmsg(f'\n  Testing authentication with credentials from {d.cfg_file}:')
		d.remove_datadir()
		os.makedirs(d.datadir)

		cf = os.path.join(d.datadir,d.cfg_file)
		open(cf,'a').write('\nrpcuser = ut_rpc\nrpcpassword = ut_rpc_passw0rd\n')

		d.add_flag('keep_cfg_file')
		d.start()

		async def do():
			rpc = await rpc_init(proto)
			assert rpc.auth.user == 'ut_rpc', f'{rpc.auth.user}: user is not ut_rpc!'

		run_session(do())
		d.stop()

def do_msg(rpc):
	qmsg('  Testing backend {!r}'.format(type(rpc.backend).__name__))

class init_test:

	async def btc(proto,backend):
		rpc = await rpc_init(proto,backend)
		do_msg(rpc)
		addrs = (
			('bc1qvmqas4maw7lg9clqu6kqu9zq9cluvlln5hw97q','test address #1'), # deadbeef * 8
			('bc1qe50rj25cldtskw5huxam335kyshtqtlrf4pt9x','test address #2'), # deadbeef * 7 + deadbeee
		)
		await rpc.batch_call('importaddress',addrs,timeout=120)
		ret = await rpc.batch_call('getaddressesbylabel',[(l,) for a,l in addrs])
		assert list(ret[0].keys())[0] == addrs[0][0]

		bh = (await rpc.call('getblockchaininfo',timeout=300))['bestblockhash']
		await rpc.gathered_call('getblock',((bh,),(bh,1)),timeout=300)
		await rpc.gathered_call(None,(('getblock',(bh,)),('getblock',(bh,1))),timeout=300)

	async def bch(proto,backend):
		rpc = await rpc_init(proto,backend)
		do_msg(rpc)

	ltc = bch

	async def eth(proto,backend):
		rpc = await rpc_init(proto,backend)
		do_msg(rpc)
		await rpc.call('parity_versionInfo',timeout=300)

def run_test(coin,auth):
	proto = init_proto(coin,network=('mainnet','regtest')[coin=='eth']) # FIXME CoinDaemon's network handling broken
	d = CoinDaemon(network_id=coin,test_suite=True)
	if auth:
		d.remove_datadir()
	d.start()

	for backend in g.autoset_opts['rpc_backend'].choices:
		run_session(getattr(init_test,coin)(proto,backend),backend=backend)

	d.stop()
	if auth:
		auth_test(proto,d)
	qmsg('  OK')
	return True

class unit_tests:

	altcoin_deps = ('ltc','bch','eth','xmr_wallet')

	def btc(self,name,ut):
		return run_test('btc',auth=True)

	def ltc(self,name,ut):
		return run_test('ltc',auth=True)

	def bch(self,name,ut):
		return run_test('bch',auth=True)

	def eth(self,name,ut):
		return run_test('eth',auth=False)

	def xmr_wallet(self,name,ut):

		async def run():
			md = CoinDaemon('xmr',test_suite=True)
			if not opt.no_daemon_autostart:
				md.start()

			wd = MoneroWalletDaemon(
				wallet_dir = 'test/trash',
				passwd     = 'ut_rpc_passw0rd',
				test_suite = True )
			wd.start()

			c = MoneroWalletRPCClient(
				host   = wd.host,
				port   = wd.rpc_port,
				user   = wd.user,
				passwd = wd.passwd )

			await c.call('get_version')

			gmsg('OK')

			wd.wait = False
			wd.stop()

			if not opt.no_daemon_stop:
				md.wait = False
				md.stop()

		run_session(run())
		return True

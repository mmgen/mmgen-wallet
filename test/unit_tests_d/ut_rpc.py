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
		await rpc.call('eth_blockNumber',timeout=300)

	etc = eth

def run_test(network_ids,test_cf_auth): # TODO: run all available networks simultaneously

	for network_id in network_ids:

		proto = init_proto(network_id=network_id)

		d = CoinDaemon(proto=proto,test_suite=True)

		if not opt.no_daemon_stop:
			d.stop()

		if not opt.no_daemon_autostart:
			d.remove_datadir()
			d.start()

		for backend in g.autoset_opts['rpc_backend'].choices:
			run_session(getattr(init_test,proto.coin.lower())(proto,backend),backend=backend)

		if not opt.no_daemon_stop:
			d.stop()

		if test_cf_auth and g.platform != 'win':
			cfg_file_auth_test(proto,d)

		qmsg('')

	return True

class unit_tests:

	altcoin_deps = ('ltc','bch','eth','etc','xmrwallet')

	def btc(self,name,ut):
		return run_test(['btc','btc_tn'],test_cf_auth=True)

	def ltc(self,name,ut):
		return run_test(['ltc','ltc_tn'],test_cf_auth=True)

	def bch(self,name,ut):
		return run_test(['bch','bch_tn'],test_cf_auth=True)

	def eth(self,name,ut):
		return run_test(['eth'],test_cf_auth=False)

	def etc(self,name,ut):
		return run_test(['etc'],test_cf_auth=False)

	def xmrwallet(self,name,ut):

		async def run():
			networks = init_proto('xmr').networks
			daemons = [(
					CoinDaemon(proto=proto,test_suite=True),
					MoneroWalletDaemon(
						proto      = proto,
						test_suite = True,
						wallet_dir = 'test/trash',
						passwd     = 'ut_rpc_passw0rd' )
				) for proto in (init_proto('xmr',network=network) for network in networks) ]

			for md,wd in daemons:
				if not opt.no_daemon_autostart:
					md.start()
				wd.start()
				c = MoneroWalletRPCClient(
					host   = wd.host,
					port   = wd.rpc_port,
					user   = wd.user,
					passwd = wd.passwd )
				await c.call('get_version')

			for md,wd in daemons:
				wd.wait = False
				wd.stop()
				if not opt.no_daemon_stop:
					md.wait = False
					md.stop()

			gmsg('OK')

		run_session(run())
		return True

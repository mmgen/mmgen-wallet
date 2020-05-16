#!/usr/bin/env python3
"""
test.unit_tests_d.ut_rpc: RPC unit test for the MMGen suite
"""

from mmgen.common import *
from mmgen.exception import *

from mmgen.protocol import init_proto
from mmgen.rpc import MoneroWalletRPCClient
from mmgen.daemon import CoinDaemon,MoneroWalletDaemon

def auth_test(d):
	d.stop()
	if g.platform != 'win':
		qmsg(f'\n  Testing authentication with credentials from bitcoin.conf:')
		d.remove_datadir()
		os.makedirs(d.datadir)

		cf = os.path.join(d.datadir,'bitcoin.conf')
		open(cf,'a').write('\nrpcuser = ut_rpc\nrpcpassword = ut_rpc_passw0rd\n')

		d.add_flag('keep_cfg_file')
		d.start()

		async def do():
			assert g.rpc.auth.user == 'ut_rpc', 'user is not ut_rpc!'

		run_session(do())
		d.stop()

class unit_tests:

	def bch(self,name,ut):

		async def run_test():
			qmsg('  Testing backend {!r}'.format(type(g.rpc.backend).__name__))

		d = CoinDaemon('bch',test_suite=True)
		d.remove_datadir()
		d.start()
		g.proto.daemon_data_dir = d.datadir # location of cookie file
		g.rpc_port = d.rpc_port

		for backend in g.autoset_opts['rpc_backend'].choices:
			run_session(run_test(),backend=backend)

		auth_test(d)
		qmsg('  OK')
		return True

	def btc(self,name,ut):

		async def run_test():
			c = g.rpc
			qmsg('  Testing backend {!r}'.format(type(c.backend).__name__))
			addrs = (
				('bc1qvmqas4maw7lg9clqu6kqu9zq9cluvlln5hw97q','test address #1'), # deadbeef * 8
				('bc1qe50rj25cldtskw5huxam335kyshtqtlrf4pt9x','test address #2'), # deadbeef * 7 + deadbeee
			)

			await c.batch_call('importaddress',addrs,timeout=120)
			ret = await c.batch_call('getaddressesbylabel',[(l,) for a,l in addrs])
			assert list(ret[0].keys())[0] == addrs[0][0]

			bh = (await c.call('getblockchaininfo',timeout=300))['bestblockhash']
			await c.gathered_call('getblock',((bh,),(bh,1)),timeout=300)
			await c.gathered_call(None,(('getblock',(bh,)),('getblock',(bh,1))),timeout=300)


		d = CoinDaemon('btc',test_suite=True)
		d.remove_datadir()
		d.start()
		g.proto.daemon_data_dir = d.datadir # used by BitcoinRPCClient.set_auth() to find the cookie
		g.rpc_port = d.rpc_port

		for backend in g.autoset_opts['rpc_backend'].choices:
			run_session(run_test(),backend=backend)

		auth_test(d)
		qmsg('  OK')
		return True

	def eth(self,name,ut):
		ed = CoinDaemon('eth',test_suite=True)
		ed.start()
		g.rpc_port = CoinDaemon('eth',test_suite=True).rpc_port

		async def run_test():
			qmsg('  Testing backend {!r}'.format(type(g.rpc.backend).__name__))
			ret = await g.rpc.call('parity_versionInfo',timeout=300)

		for backend in g.autoset_opts['rpc_backend'].choices:
			run_session(run_test(),proto=init_proto('eth'),backend=backend)

		ed.stop()
		return True

	def xmr_wallet(self,name,ut):

		async def run():
			md = CoinDaemon('xmr',test_suite=True)
			if not opt.no_daemon_autostart:
				md.start()

			g.monero_wallet_rpc_password = 'passwOrd'
			mwd = MoneroWalletDaemon(wallet_dir='test/trash',test_suite=True)
			mwd.start()

			c = MoneroWalletRPCClient(
				host = g.monero_wallet_rpc_host,
				port = mwd.rpc_port,
				user = g.monero_wallet_rpc_user,
				passwd = g.monero_wallet_rpc_password)

			await c.call('get_version')

			gmsg('OK')

			mwd.wait = False
			mwd.stop()

			if not opt.no_daemon_stop:
				md.wait = False
				md.stop()

		run_session(run(),do_rpc_init=False)
		return True

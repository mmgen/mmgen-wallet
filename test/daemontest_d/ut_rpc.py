#!/usr/bin/env python3

"""
test.daemontest_d.ut_rpc: RPC unit test for the MMGen suite
"""

import sys, os

from mmgen.cfg import Config
from mmgen.color import yellow, cyan
from mmgen.util import msg, gmsg, make_timestr, pp_fmt, die
from mmgen.protocol import init_proto
from mmgen.rpc import rpc_init
from mmgen.daemon import CoinDaemon
from mmgen.proto.xmr.rpc import MoneroRPCClient, MoneroWalletRPCClient
from mmgen.proto.xmr.daemon import MoneroWalletDaemon

from ..include.common import cfg, qmsg, vmsg

async def cfg_file_auth_test(cfg, d, bad_auth=False):
	m = 'missing credentials' if bad_auth else f'credentials from {d.cfg_file}'
	qmsg(cyan(f'\n  Testing authentication with {m}:'))
	d.stop()
	d.remove_datadir() # removes cookie file to force authentication from cfg file
	os.makedirs(d.network_datadir)

	if not bad_auth:
		cf = os.path.join(d.datadir, d.cfg_file)
		with open(cf, 'a') as fp:
			fp.write('\nrpcuser = ut_rpc\nrpcpassword = ut_rpc_passw0rd\n')
		d.flag.keep_cfg_file = True

	d.start()

	if bad_auth:
		os.rename(d.auth_cookie_fn, d.auth_cookie_fn+'.bak')
		try:
			await rpc_init(cfg, d.proto)
		except Exception as e:
			vmsg(yellow(str(e)))
		else:
			die(3, 'No error on missing credentials!')
		os.rename(d.auth_cookie_fn+'.bak', d.auth_cookie_fn)
	else:
		rpc = await rpc_init(cfg, d.proto)
		assert rpc.auth.user == 'ut_rpc', f'{rpc.auth.user}: user is not ut_rpc!'

	if not cfg.no_daemon_stop:
		d.stop()
		d.remove_datadir()

async def print_daemon_info(rpc):

	if rpc.proto.base_proto == 'Monero':
		msg(f"""
    DAEMON VERSION: {rpc.daemon_version} [{rpc.daemon_version_str}]
    NETWORK:        {rpc.proto.coin} {rpc.proto.network.upper()}
		""".rstrip())
	else:
		msg(f"""
    DAEMON VERSION: {rpc.daemon_version} [{rpc.daemon_version_str}]
    CAPS:           {rpc.caps}
    NETWORK:        {rpc.proto.coin} {rpc.proto.network.upper()}
    CHAIN:          {rpc.chain}
    BLOCKCOUNT:     {rpc.blockcount}
    CUR_DATE:       {rpc.cur_date} [{make_timestr(rpc.cur_date)}]
		""".rstrip())

	if rpc.proto.base_proto == 'Bitcoin':
		def fmt_dict(d):
			return '\n        ' + '\n        '.join(pp_fmt(d).split('\n')) + '\n'
		msg(f"""
    NETWORKINFO:    {fmt_dict(rpc.cached["networkinfo"])}
    BLOCKCHAININFO: {fmt_dict(rpc.cached["blockchaininfo"])}
    DEPLOYMENTINFO: {fmt_dict(rpc.cached["deploymentinfo"])}
    WALLETINFO:     {fmt_dict(await rpc.walletinfo)}
		""".rstrip())

	msg('')

def do_msg(rpc, backend):
	bname = type(rpc.backend).__name__
	qmsg('  Testing backend {!r}{}'.format(bname, '' if backend == bname else f' [{backend}]'))

class init_test:

	@staticmethod
	async def btc(cfg, daemon, backend):
		rpc = await rpc_init(cfg, daemon.proto, backend, daemon)
		do_msg(rpc, backend)

		if cfg.tw_name:
			wi = await rpc.walletinfo
			assert wi['walletname'] == rpc.cfg.tw_name, f'{wi["walletname"]!r} != {rpc.cfg.tw_name!r}'

		bh = (await rpc.call('getblockchaininfo', timeout=300))['bestblockhash']
		await rpc.gathered_call('getblock', ((bh,), (bh, 1)), timeout=300)
		await rpc.gathered_call(None, (('getblock', (bh,)), ('getblock', (bh, 1))), timeout=300)
		return rpc

	@staticmethod
	async def bch(cfg, daemon, backend):
		rpc = await rpc_init(cfg, daemon.proto, backend, daemon)
		do_msg(rpc, backend)
		return rpc

	ltc = bch

	@staticmethod
	async def eth(cfg, daemon, backend):
		rpc = await rpc_init(cfg, daemon.proto, backend, daemon)
		do_msg(rpc, backend)
		await rpc.call('eth_blockNumber', timeout=300)
		return rpc

	etc = eth

async def run_test(network_ids, test_cf_auth=False, daemon_ids=None, cfg_in=None):

	async def do_test(d, cfg):

		d.wait = True

		if not cfg.no_daemon_stop:
			d.stop()
			d.remove_datadir()

		if not cfg.no_daemon_autostart:
			d.remove_datadir()
			d.start()

		for n, backend in enumerate(cfg._autoset_opts['rpc_backend'].choices):
			test = getattr(init_test, d.proto.coin.lower())
			rpc = await test(cfg, d, backend)
			if not n and cfg.verbose:
				await print_daemon_info(rpc)

		if not cfg.no_daemon_stop:
			d.stop()
			d.remove_datadir()

		if test_cf_auth and sys.platform != 'win32':
			await cfg_file_auth_test(cfg, d)
			await cfg_file_auth_test(cfg, d, bad_auth=True)

		qmsg('')

	cfg_arg = cfg_in or cfg

	for network_id in network_ids:
		proto = init_proto(cfg_arg, network_id=network_id)
		all_ids = CoinDaemon.get_daemon_ids(cfg_arg, proto.coin)
		ids = set(daemon_ids) & set(all_ids) if daemon_ids else all_ids
		for daemon_id in ids:
			await do_test(CoinDaemon(cfg_arg, proto=proto, test_suite=True, daemon_id=daemon_id), cfg_arg)

	return True

class unit_tests:

	altcoin_deps = ('ltc', 'bch', 'geth', 'erigon', 'parity', 'xmrwallet')
	arm_skip = ('parity',) # no prebuilt binaries for ARM

	async def btc(self, name, ut):
		return await run_test(
			['btc', 'btc_tn'],
			test_cf_auth = True,
			cfg_in = Config({'_clone': cfg, 'tw_name': 'alternate-tracking-wallet'}))

	async def ltc(self, name, ut):
		return await run_test(['ltc', 'ltc_tn'], test_cf_auth=True)

	async def bch(self, name, ut):
		return await run_test(['bch', 'bch_tn'], test_cf_auth=True)

	async def geth(self, name, ut):
		# mainnet returns EIP-155 error on empty blockchain:
		return await run_test(['eth_tn', 'eth_rt'], daemon_ids=['geth'])

	async def erigon(self, name, ut):
		return await run_test(['eth', 'eth_tn', 'eth_rt'], daemon_ids=['erigon'])

	async def parity(self, name, ut):
		return await run_test(['etc'])

	async def xmrwallet(self, name, ut):

		async def test_monerod_rpc(md):
			rpc = MoneroRPCClient(
				cfg    = cfg,
				proto  = md.proto,
				host   = 'localhost',
				port   = md.rpc_port,
				user   = None,
				passwd = None,
				daemon = md,
			)
			if cfg.verbose:
				await print_daemon_info(rpc)
			rpc.call_raw('get_height')
			rpc.call('get_last_block_header')

		from mmgen.xmrseed import xmrseed

		async def run():
			networks = init_proto(cfg, 'xmr').networks
			daemons = [(
					CoinDaemon(cfg, proto=proto, test_suite=True),
					MoneroWalletDaemon(
						cfg        = cfg,
						proto      = proto,
						test_suite = True,
						wallet_dir = os.path.join('test', 'trash2'),
						datadir    = os.path.join('test', 'trash2', 'wallet_rpc'),
						passwd     = 'ut_rpc_passw0rd')
				) for proto in (init_proto(cfg, 'xmr', network=network) for network in networks)]

			for md, wd in daemons:
				if not cfg.no_daemon_autostart:
					md.start()
				wd.start()

				await test_monerod_rpc(md)

				c = MoneroWalletRPCClient(cfg=cfg, daemon=wd)
				fn = f'monero-{wd.network}-junk-wallet'
				qmsg(f'Creating {wd.network} wallet')
				c.call(
					'restore_deterministic_wallet',
					filename = fn,
					password = 'foo',
					seed     = xmrseed().fromhex('beadface'*8, tostr=True))

				if sys.platform == 'win32':
					wd.stop()
					wd.start()

				qmsg(f'Opening {wd.network} wallet')
				c.call('open_wallet', filename=fn, password='foo')

				await c.stop_daemon()

				if not cfg.no_daemon_stop:
					if sys.platform == 'darwin':
						md.stop()
					else:
						await md.rpc.stop_daemon()

			gmsg('OK')

		import shutil
		shutil.rmtree('test/trash2', ignore_errors=True)
		os.makedirs('test/trash2/wallet_rpc')
		await run()
		return True

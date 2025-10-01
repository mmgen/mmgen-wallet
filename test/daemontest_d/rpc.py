#!/usr/bin/env python3

"""
test.daemontest_d.rpc: RPC unit test for the MMGen suite
"""

import sys, os, asyncio

from mmgen.cfg import Config
from mmgen.color import yellow, cyan
from mmgen.util import msg, gmsg, make_timestr, pp_fmt, die, async_run
from mmgen.protocol import init_proto
from mmgen.rpc import rpc_init
from mmgen.daemon import CoinDaemon
from mmgen.proto.xmr.rpc import MoneroRPCClient, MoneroWalletRPCClient
from mmgen.proto.xmr.daemon import MoneroWalletDaemon

from ..include.common import cfg, qmsg, vmsg, in_nix_environment, test_exec

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

	msg(f'    BIND_PORT:      {rpc.daemon.bind_port}')

	if rpc.proto.base_proto == 'Bitcoin':
		def fmt_dict(d):
			return '\n        ' + '\n        '.join(pp_fmt(d).split('\n')) + '\n'
		msg(f"""
    NETWORKINFO:    {fmt_dict(rpc.cached["networkinfo"])}
    BLOCKCHAININFO: {fmt_dict(rpc.cached["blockchaininfo"])}
    DEPLOYMENTINFO: {fmt_dict(rpc.cached["deploymentinfo"])}
    WALLETINFO:     {fmt_dict(await rpc.walletinfo)}
		""".rstrip())

	if rpc.proto.base_proto == 'Ethereum':
		msg(f'    CHAIN_NAMES:    {" ".join(rpc.daemon.proto.chain_names)}')

	msg('')

def do_msg(rpc, backend):
	bname = type(rpc.backend).__name__
	qmsg('  Testing backend {!r}{}'.format(bname, '' if backend == bname else f' [{backend}]'))

class init_test:

	@staticmethod
	async def btc(cfg, daemon, backend, cfg_override):
		rpc = await rpc_init(cfg, daemon.proto, backend=backend, daemon=daemon)
		do_msg(rpc, backend)

		wi = await rpc.walletinfo
		assert wi['walletname'] == cfg_override['btc_tw_name']
		assert wi['walletname'] == rpc.cfg._proto.tw_name, f'{wi["walletname"]!r} != {rpc.cfg._proto.tw_name!r}'
		assert daemon.bind_port == cfg_override['btc_rpc_port']

		bh = (await rpc.call('getblockchaininfo', timeout=300))['bestblockhash']
		await rpc.gathered_call('getblock', ((bh,), (bh, 1)), timeout=300)
		await rpc.gathered_call(None, (('getblock', (bh,)), ('getblock', (bh, 1))), timeout=300)
		return rpc

	@staticmethod
	async def bch(cfg, daemon, backend, cfg_override):
		rpc = await rpc_init(cfg, daemon.proto, backend=backend, daemon=daemon)
		do_msg(rpc, backend)
		return rpc

	ltc = bch

	@staticmethod
	async def eth(cfg, daemon, backend, cfg_override):
		rpc = await rpc_init(cfg, daemon.proto, backend=backend, daemon=daemon)
		do_msg(rpc, backend)
		await rpc.call('eth_blockNumber', timeout=300)
		if rpc.proto.network == 'testnet':
			assert daemon.proto.chain_names == cfg_override['eth_testnet_chain_names']
			assert daemon.bind_port == cfg_override['eth_rpc_port']
		return rpc

	etc = eth

def run_test(network_ids, test_cf_auth=False, daemon_ids=None, cfg_override=None):

	def do_test(d, cfg):

		d.wait = True

		if not cfg.no_daemon_stop:
			d.stop()
			d.remove_datadir()

		if not cfg.no_daemon_autostart:
			d.remove_datadir()
			d.start()

		for n, backend in enumerate(cfg._autoset_opts['rpc_backend'].choices):
			test = getattr(init_test, d.proto.coin.lower())
			cfg_b = Config({'_clone': cfg, 'rpc_backend': backend})
			rpc = async_run(cfg_b, test, args=(cfg_b, d, backend, cfg_override))
			if not n and cfg.verbose:
				asyncio.run(print_daemon_info(rpc))

		if not cfg.no_daemon_stop:
			d.stop()
			d.remove_datadir()

		if test_cf_auth and sys.platform != 'win32':
			asyncio.run(cfg_file_auth_test(cfg, d))
			asyncio.run(cfg_file_auth_test(cfg, d, bad_auth=True))

		qmsg('')

	my_cfg = Config(cfg_override) if cfg_override else cfg

	for network_id in network_ids:
		proto = init_proto(my_cfg, network_id=network_id)
		all_ids = CoinDaemon.get_daemon_ids(my_cfg, proto.coin)
		ids = set(daemon_ids) & set(all_ids) if daemon_ids else all_ids
		for daemon_id in ids:
			do_test(CoinDaemon(my_cfg, proto=proto, test_suite=True, daemon_id=daemon_id), my_cfg)

	return True

class unit_tests:

	altcoin_deps = ('ltc', 'bch', 'geth', 'reth', 'erigon', 'parity', 'xmrwallet')
	arm_skip = ('parity',) # no prebuilt binaries for ARM
	riscv_skip = ('parity',) # no prebuilt binaries for RISC-V
	fast_skip = ('reth', 'erigon')

	def btc(self, name, ut):
		return run_test(
			['btc', 'btc_tn'],
			test_cf_auth = True,
			cfg_override = {
				'_clone': cfg,
				'btc_rpc_port': 19777,
				'rpc_port':     32323, # ignored
				'btc_tw_name': 'alternate-tracking-wallet',
				'tw_name':     'this-is-overridden',
				'ltc_tw_name': 'this-is-ignored',
				'eth_mainnet_chain_names': ['also', 'ignored'],
		})

	def ltc(self, name, ut):
		return run_test(['ltc', 'ltc_tn'], test_cf_auth=True)

	def bch(self, name, ut):
		return run_test(['bch', 'bch_tn'], test_cf_auth=True)

	def geth(self, name, ut):
		# mainnet returns EIP-155 error on empty blockchain:
		return run_test(
			['eth_tn', 'eth_rt'],
			daemon_ids = ['geth'],
			cfg_override = {
				'_clone': cfg,
				'eth_rpc_port': 19777,
				'rpc_port':     32323, # ignored
				'btc_tw_name': 'ignored',
				'tw_name':     'also-ignored',
				'eth_testnet_chain_names': ['goerli', 'holesky', 'foo', 'bar', 'baz'],
		})

	def reth(self, name, ut):
		return run_test(['eth', 'eth_rt'], daemon_ids=['reth']) # TODO: eth_tn

	def erigon(self, name, ut):
		return run_test(['eth', 'eth_tn', 'eth_rt'], daemon_ids=['erigon'])

	def parity(self, name, ut):
		if in_nix_environment() and not test_exec('parity --help'):
			ut.skip_msg('Nix environment')
			return True
		return run_test(['etc'])

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
					md.stop()

			gmsg('OK')

		import shutil
		shutil.rmtree('test/trash2', ignore_errors=True)
		os.makedirs('test/trash2/wallet_rpc')
		await run()
		return True

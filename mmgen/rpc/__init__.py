#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
rpc: RPC library for the MMGen Project
"""

import importlib

from ..util import die, fmt, fmt_list
from ..obj import NonNegativeInt

async def rpc_init(
		cfg,
		proto                 = None,
		*,
		backend               = None,
		daemon                = None,
		ignore_daemon_version = False,
		ignore_wallet         = False):

	proto = proto or cfg._proto

	if not 'rpc_init' in proto.mmcaps:
		die(1, f'rpc_init() not supported for {proto.name} protocol!')

	if proto.rpc_type == 'remote':
		return getattr(importlib.import_module(
			f'mmgen.proto.{proto.base_proto_coin.lower()}.rpc.remote'),
				proto.base_proto + 'RemoteRPCClient')(cfg=cfg, proto=proto)

	from ..daemon import CoinDaemon

	rpc = await getattr(importlib.import_module(
			f'mmgen.proto.{proto.base_proto_coin.lower()}.rpc.local'),
				proto.base_proto + 'RPCClient')(
		cfg           = cfg,
		proto         = proto,
		daemon        = daemon or CoinDaemon(cfg, proto=proto, test_suite=cfg.test_suite),
		backend       = backend or cfg.rpc_backend,
		ignore_wallet = ignore_wallet)

	if rpc.daemon_version > rpc.daemon.coind_version:
		rpc.handle_unsupported_daemon_version(
			proto.name,
			ignore_daemon_version or proto.ignore_daemon_version or cfg.ignore_daemon_version)

	if rpc.chain not in proto.chain_names:
		die('RPCChainMismatch', '\n' + fmt(f"""
			Protocol:           {proto.cls_name}
			Valid chain names:  {fmt_list(proto.chain_names, fmt='bare')}
			RPC client chain:   {rpc.chain}
			""", indent='  ').rstrip())

	rpc.blockcount = NonNegativeInt(rpc.blockcount)

	return rpc

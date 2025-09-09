#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
#
# Project source code repository: https://github.com/mmgen/mmgen-wallet
# Licensed according to the terms of GPL Version 3.  See LICENSE for details.

"""
test.cmdtest_d.opts: options processing tests for the MMGen cmdtest.py test suite
"""

import os, time

from .base import CmdTestBase

class CmdTestOpts(CmdTestBase):
	'command-line options parsing and processing'
	networks = ('btc',)
	tmpdir_nums = [41]
	cmd_group = (
		('opt_helpscreen',       (41, 'helpscreen output', [])),
		('opt_noargs',           (41, 'invocation with no user options or arguments', [])),
		('opt_good1',            (41, 'good opts (long opts only)', [])),
		('opt_good2',            (41, 'good opts (mixed short and long opts)', [])),
		('opt_good3',            (41, 'good opts (max arg count)', [])),
		('opt_good4',            (41, 'good opts (maxlen arg)', [])),
		('opt_good5',            (41, 'good opts (long opt substring)', [])),
		('opt_good6',            (41, 'good global opt (--coin=xmr)', [])),
		('opt_good7',            (41, 'good global opt (--coin xmr)', [])),
		('opt_good8',            (41, 'good global opt (--pager)', [])),
		('opt_good9',            (41, 'good cmdline arg ‘-’', [])),
		('opt_good10',           (41, 'good cmdline arg ‘-’ with arg', [])),
		('opt_good11',           (41, 'good cmdline arg ‘-’ with option', [])),
		('opt_good12',           (41, 'good cmdline opt (short opt with option)', [])),
		('opt_good13',           (41, 'good cmdline opt (short opt with option)', [])),
		('opt_good14',           (41, 'good cmdline opt (combined short opt with option)', [])),
		('opt_good15',           (41, 'good cmdline opt (combined short opt with option)', [])),
		('opt_good16',           (41, 'good cmdline opt (param with equals signs)', [])),
		('opt_good17',           (41, 'good cmdline opt (param with equals signs)', [])),
		('opt_good18',           (41, 'good cmdline opt (param with equals signs)', [])),
		('opt_good19',           (41, 'good cmdline opt (param with equals signs)', [])),
		('opt_good20',           (41, 'good cmdline opt (opt + negated opt)', [])),
		('opt_good21',           (41, 'good cmdline opt (negated negative opt)', [])),
		('opt_good22',           (41, 'good cmdline opt (opt + negated opt [substring])', [])),
		('opt_good23',           (41, 'good cmdline opt (negated negative opt [substring])', [])),
		('opt_good24',           (41, 'good cmdline opt (negated opt + opt [substring])', [])),
		('opt_good25',           (41, 'good cmdline opt (--btc-rpc-host)', [])),
		('opt_good26',           (41, 'good cmdline opt (--btc-rpc-port)', [])),
		('opt_good27',           (41, 'good cmdline opt (--btc-ignore-daemon-version)', [])),
		('opt_good28',           (41, 'good cmdline opt (--bch-cashaddr)', [])),
		('opt_good29',           (41, 'good cmdline opt (--etc-max-tx-fee=0.1)', [])),
		('opt_good30',           (41, 'good cmdline opt (--eth-chain-names=foo,bar)', [])),
		('opt_good31',           (41, 'good cmdline opt (--xmr-rpc-port=28081)', [])),
		('opt_bad_param',        (41, 'bad global opt (--pager=1)', [])),
		('opt_bad_infile',       (41, 'bad infile parameter', [])),
		('opt_bad_outdir',       (41, 'bad outdir parameter', [])),
		('opt_bad_incompatible', (41, 'incompatible opts', [])),
		('opt_bad_autoset',      (41, 'invalid autoset value', [])),
		('opt_invalid_1',        (41, 'invalid cmdline opt ‘--x’', [])),
		('opt_invalid_2',        (41, 'invalid cmdline opt ‘---’', [])),
		('opt_invalid_5',        (41, 'invalid cmdline opt (missing parameter)', [])),
		('opt_invalid_6',        (41, 'invalid cmdline opt (missing parameter)', [])),
		('opt_invalid_7',        (41, 'invalid cmdline opt (parameter not required)', [])),
		('opt_invalid_8',        (41, 'invalid cmdline opt (non-existent option)', [])),
		('opt_invalid_9',        (41, 'invalid cmdline opt (non-existent option)', [])),
		('opt_invalid_10',       (41, 'invalid cmdline opt (missing parameter)', [])),
		('opt_invalid_11',       (41, 'invalid cmdline opt (missing parameter)', [])),
		('opt_invalid_12',       (41, 'invalid cmdline opt (non-existent option)', [])),
		('opt_invalid_13',       (41, 'invalid cmdline opt (ambiguous long opt substring)', [])),
		('opt_invalid_14',       (41, 'invalid cmdline opt (long opt substring too short)', [])),
		('opt_invalid_15',       (41, 'invalid cmdline (too many args)', [])),
		('opt_invalid_16',       (41, 'invalid cmdline (overlong arg)', [])),
		('opt_invalid_17',       (41, 'invalid cmdline opt (--btc-rpc-host without ‘need_proto’)', [])),
		('opt_invalid_18',       (41, 'invalid cmdline opt (--btc-rpc-port without ‘need_proto’)', [])),
		('opt_invalid_19',       (41, 'invalid cmdline opt (--btc-rpc-port with non-integer param)', [])),
		('opt_invalid_21',       (41, 'invalid cmdline opt (--btc-foo)', [])),
		('opt_invalid_22',       (41, 'invalid cmdline opt (--btc-rpc-host with missing param)', [])),
		('opt_invalid_23',       (41, 'invalid cmdline opt (--btc-ignore-daemon-version with param)', [])),
		('opt_invalid_24',       (41, 'invalid cmdline opt (--bch-cashaddr without ‘need_proto’)', [])),
		('opt_invalid_25',       (41, 'invalid cmdline opt (--bch-cashaddr without parameter)', [])),
		('opt_invalid_26',       (41, 'invalid cmdline opt (--bch-cashaddr with non-bool parameter)', [])),
		('opt_invalid_27',       (41, 'invalid cmdline opt (--ltc-cashaddr)', [])),
		('opt_invalid_28',       (41, 'invalid cmdline opt (--xmr-max-tx-fee)', [])),
		('opt_invalid_29',       (41, 'invalid cmdline opt (--eth-max-tx-fee without parameter)', [])),
		('opt_invalid_30',       (41, 'invalid cmdline opt (--eth-max-tx-fee with non-numeric parameter)', [])),
		('opt_invalid_31',       (41, 'invalid cmdline opt (--bch-cashaddr without --coin=bch)', [])),
		('opt_invalid_32',       (41, 'invalid cmdline opt (--eth-chain-names without --coin=eth)', [])),
		('opt_invalid_33',       (41, 'invalid cmdline opt (--xmr-rpc-host)', [])),
		('opt_invalid_34',       (41, 'invalid cmdline opt (--eth-rpc-user)', [])),
	)

	def spawn_prog(self, args, opts=[], exit_val=None, need_proto=False):
		return self.spawn(
			'test/misc/opts.py',
			opts + args,
			cmd_dir  = '.',
			exit_val = exit_val,
			env      = {'TEST_MISC_OPTS_NEEDS_PROTO': '1' if need_proto else ''})

	def check_vals(self, args, vals, check=True, need_proto=False):
		show_opts = [a.removeprefix('cfg.') for a, b in vals if a.startswith('cfg.')]
		t = self.spawn_prog(
			args,
			opts       = ['--show-opts=' + ','.join(show_opts)] if show_opts else [],
			need_proto = need_proto)
		if check:
			for k, v in vals:
				t.expect(rf'{k}:\s+{v}', regex=True)
		return t

	def do_run(self, args, expect, exit_val, regex=False):
		t = self.spawn_prog(args, exit_val=exit_val or None)
		t.expect(expect, regex=regex)
		return t

	def opt_helpscreen(self):
		expect = r'OPTS.PY: Opts test.*USAGE:\s+opts.py'
		if not self.cfg.pexpect_spawn:
			expect += r'.*--minconf.*NOTES FOR THIS.*a note'
		t = self.do_run(['--help'], expect, 0, regex=True)
		if t.pexpect_spawn:
			time.sleep(0.4)
			t.send('q')
		return t

	def opt_noargs(self):
		return self.check_vals(
			[],
			(
				('cfg.foo',                 'None'),         # added opt
				('cfg.print_checksum',      'None'),         # sets 'quiet'
				('cfg.quiet',               'False'),        # _incompatible_opts
				('cfg.verbose',             'False'),        # _incompatible_opts
				('cfg.passwd_file',         ''),             # _infile_opts - check_infile()
				('cfg.outdir',              ''),             # check_outdir()
				('cfg.cached_balances',     'False'),
				('cfg.minconf',             '1'),
				('cfg.coin',                'BTC'),
				('cfg.pager',               'False'),
				('cfg.fee_estimate_mode',   'conservative'), # _autoset_opts
			))

	def opt_good1(self):
		pf_base = 'testfile'
		pf = os.path.join(self.tmpdir, pf_base)
		self.write_to_tmpfile(pf_base, '')
		return self.check_vals(
			[
				'--print-checksum',
				'--fee-estimate-mode=E',
				'--passwd-file='+pf,
				'--outdir='+self.tmpdir,
				'--cached-balances',
				f'--hidden-incog-input-params={pf},123',
			], (
				('cfg.print_checksum',           'True'),
				('cfg.quiet',                    'True'), # set by print_checksum
				('cfg.passwd_file',              pf),
				('cfg.outdir',                   self.tmpdir),
				('cfg.cached_balances',          'True'),
				('cfg.hidden_incog_input_params', pf+',123'),
				('cfg.fee_estimate_mode',         'economical'),
			))

	def opt_good2(self):
		return self.check_vals(
			[
				'--print-checksum',
				'-qX',
				f'--outdir={self.tmpdir}',
				'-p5',
				'-m', '0',
				'--seed-len=256',
				'-L--my-label',
				'--seed-len', '128',
				'--min-temp=-30',
				'-T-10',
				'--',
				'x', 'y', '12345'
			], (
				('cfg.print_checksum',  'True'),
				('cfg.quiet',           'True'),
				('cfg.outdir',          self.tmpdir),
				('cfg.cached_balances', 'True'),
				('cfg.minconf',         '0'),
				('cfg.keep_label',      'None'),
				('cfg.seed_len',        '128'),
				('cfg.hash_preset',     '5'),
				('cfg.label',           '--my-label'),
				('cfg.min_temp',        '-30'),
				('cfg.max_temp',        '-10'),
				('arg1',                'x'),
				('arg2',                'y'),
				('arg3',                '12345'),
			))

	def opt_good3(self):
		return self.check_vals(['m'] * 256, (('arg256', 'm'),))

	def opt_good4(self):
		return self.check_vals(['e' * 4096], (('arg1', 'e' * 4096),))

	def opt_good5(self):
		return self.check_vals(['--minc=7'], (('cfg.minconf', '7'),))

	def opt_good6(self):
		if self.cfg.no_altcoin:
			return 'skip'
		return self.check_vals(['--coin=xmr'], (('cfg.coin', 'XMR'),))

	def opt_good7(self):
		if self.cfg.no_altcoin:
			return 'skip'
		return self.check_vals(['--coin', 'xmr'], (('cfg.coin', 'XMR'),))

	def opt_good8(self):
		return self.check_vals(['--pager'], (('cfg.pager', 'True'),))

	def opt_good9(self):
		return self.check_vals(['-'], (('arg1', '-'),))

	def opt_good10(self):
		return self.check_vals(['-', '-x'], (('arg1', '-'), ('arg2', '-x')))

	def opt_good11(self):
		return self.check_vals(['-q', '-', '-x'], (('arg1', '-'), ('arg2', '-x')))

	def opt_good12(self):
		return self.check_vals(['-l128'], (('cfg.seed_len', '128'),))

	def opt_good13(self):
		return self.check_vals(['-l', '128'], (('cfg.seed_len', '128'),))

	def opt_good14(self):
		return self.check_vals(['-kl128'], (('cfg.keep_label', 'True'), ('cfg.seed_len', '128')))

	def opt_good15(self):
		return self.check_vals(['-kl', '128'], (('cfg.keep_label', 'True'), ('cfg.seed_len', '128')))

	def opt_good16(self):
		return self.check_vals(['--point=x=1,y=2,z=3'], (('cfg.point', 'x=1,y=2,z=3'),))

	def opt_good17(self):
		return self.check_vals(['--point', 'x=1,y=2,z=3'], (('cfg.point', 'x=1,y=2,z=3'),))

	def opt_good18(self):
		return self.check_vals(['-xx=1,y=2,z=3'], (('cfg.point', 'x=1,y=2,z=3'),))

	def opt_good19(self):
		return self.check_vals(['-x', 'x=1,y=2,z=3'], (('cfg.point', 'x=1,y=2,z=3'),))

	def opt_good20(self):
		return self.check_vals(['--pager', '--no-pager'], (('cfg.pager', 'False'),))

	def opt_good21(self):
		return self.check_vals(['--foobleize'], (('cfg.no_foobleize', 'False'),))

	def opt_good22(self):
		return self.check_vals(['--quiet', '--no-q'], (('cfg.quiet', 'False'),))

	def opt_good23(self):
		return self.check_vals(['--foobl'], (('cfg.no_foobleize', 'False'),))

	def opt_good24(self):
		return self.check_vals(['--no-pag', '--pag'], (('cfg.pager', 'True'),))

	def opt_good25(self):
		return self.check_vals(
			['--btc-rpc-host=pi5'],
			(('cfg.btc_rpc_host', 'pi5'), ('proto.rpc_host', 'pi5')),
			need_proto=True)

	def opt_good26(self):
		return self.check_vals(
			['--btc-rpc-port=7272'],
			(('cfg.btc_rpc_port', '7272'), ('proto.rpc_port', '7272')),
			need_proto=True)

	def opt_good27(self):
		return self.check_vals(
			['--btc-ignore-daemon-version'],
			(('cfg.btc_ignore_daemon_version', 'True'), ('proto.ignore_daemon_version', 'True'),),
			need_proto = True)

	def opt_good28(self):
		return self.check_vals(
			['--coin=bch', '--bch-cashaddr=yes'],
			(('cfg.bch_cashaddr', 'True'), ('proto.cashaddr', 'True'),),
			need_proto = True)

	def opt_good29(self):
		return self.check_vals(['--etc-max-tx-fee=0.1'], (('cfg.etc_max_tx_fee', '0.1'),), need_proto=True)

	def opt_good30(self):
		if self.cfg.no_altcoin:
			return 'skip'
		return self.check_vals(
			['--coin=eth', '--eth-mainnet-chain-names=foo,bar'],
			(('cfg.eth_mainnet_chain_names', r"\['foo', 'bar'\]"), ('proto.chain_names', r"\['foo', 'bar'\]")),
			need_proto = True)

	def opt_good31(self):
		if self.cfg.no_altcoin:
			return 'skip'
		return self.check_vals(
			['--coin=xmr', '--xmr-rpc-port=28081'],
			(('cfg.xmr_rpc_port', '28081'),('proto.rpc_port', '28081'),),
			need_proto = True)

	def opt_bad_param(self):
		return self.do_run(['--pager=1'], 'no parameter', 1)

	def opt_bad_infile(self):
		pf = os.path.join(self.tmpdir, 'fubar')
		return self.do_run(['--passwd-file='+pf], 'not found', 1)

	def opt_bad_outdir(self):
		bo = self.tmpdir+'_fubar'
		return self.do_run(['--outdir='+bo], 'not found', 1)

	def opt_bad_incompatible(self):
		return self.do_run(['--label=Label', '--keep-label'], 'Conflicting options', 1)

	def opt_bad_autoset(self):
		return self.do_run(['--fee-estimate-mode=Fubar'], 'not unique substring', 1)

	def opt_invalid(self, args, expect, opts=[], need_proto=False, exit_val=1):
		t = self.spawn_prog(args, opts=opts, exit_val=exit_val, need_proto=need_proto)
		t.expect(expect)
		return t

	def opt_invalid_1(self):
		return self.opt_invalid(['--x'], 'must be at least')

	def opt_invalid_2(self):
		return self.opt_invalid(['---'], 'must be at least')

	def opt_invalid_5(self):
		return self.opt_invalid(['-l'], 'missing parameter')

	def opt_invalid_6(self):
		return self.opt_invalid(['-l', '-k'], 'missing parameter')

	def opt_invalid_7(self):
		return self.opt_invalid(['--quiet=1'], 'requires no parameter')

	def opt_invalid_8(self):
		return self.opt_invalid(['-w'], 'unrecognized option')

	def opt_invalid_9(self):
		return self.opt_invalid(['--frobnicate'], 'unrecognized option')

	def opt_invalid_10(self):
		return self.opt_invalid(['--label', '-q'], 'missing parameter')

	def opt_invalid_11(self):
		return self.opt_invalid(['-T', '-10'], 'missing parameter')

	def opt_invalid_12(self):
		return self.opt_invalid(['-q', '-10'], 'unrecognized option')

	def opt_invalid_13(self):
		return self.opt_invalid(['--mi=3'], 'ambiguous option')

	def opt_invalid_14(self):
		return self.opt_invalid(['--m=3'], 'must be at least')

	def opt_invalid_15(self):
		return self.opt_invalid(['m'] * 257, 'too many')

	def opt_invalid_16(self):
		return self.opt_invalid(['e' * 4097], 'too long')

	def opt_invalid_17(self):
		return self.opt_invalid(['--btc-rpc-host'], 'unrecognized option')

	def opt_invalid_18(self):
		return self.opt_invalid(['--btc-rpc-port'], 'unrecognized option')

	def opt_invalid_19(self):
		return self.opt_invalid(['--btc-rpc-port=foo'], "must be of type 'int'", need_proto=True)

	def opt_invalid_21(self):
		return self.opt_invalid(['--btc-foo'], 'unrecognized option')

	def opt_invalid_22(self):
		return self.opt_invalid(['--btc-rpc-host'], 'missing parameter', need_proto=True)

	def opt_invalid_23(self):
		return self.opt_invalid(['--btc-ignore-daemon-version=1'], 'requires no parameter', need_proto=True)

	def opt_invalid_24(self):
		return self.opt_invalid(['--bch-cashaddr'], 'unrecognized option')

	def opt_invalid_25(self):
		return self.opt_invalid(['--bch-cashaddr'], 'missing parameter', need_proto=True)

	def opt_invalid_26(self):
		return self.opt_invalid(['--bch-cashaddr=foo'], "must be of type 'bool'", need_proto=True)

	def opt_invalid_27(self):
		return self.opt_invalid(['--ltc-cashaddr'], 'unrecognized option', need_proto=True)

	def opt_invalid_28(self):
		return self.opt_invalid(['--xmr-max-tx-fee=0.1'], 'unrecognized option', need_proto=True)

	def opt_invalid_29(self):
		return self.opt_invalid(['--eth-max-tx-fee'], 'missing parameter', need_proto=True)

	def opt_invalid_30(self):
		return self.opt_invalid(['--eth-max-tx-fee=true'], 'must be of type', need_proto=True)

	def opt_invalid_31(self):
		return self.opt_invalid(['--bch-cashaddr=true'], 'has no attribute', opts=['--show-opts=bch_cashaddr'], need_proto=True)

	def opt_invalid_32(self):
		return self.opt_invalid(['--eth-chain-names=foo,bar'], 'unrecognized option', need_proto=True)

	def opt_invalid_33(self):
		return self.opt_invalid(['--xmr-rpc-host=solaris'], 'unrecognized option', need_proto=True)

	def opt_invalid_34(self):
		return self.opt_invalid(['--eth-rpc-user=bob'], 'unrecognized option', need_proto=True)

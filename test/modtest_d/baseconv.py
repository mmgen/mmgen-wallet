#!/usr/bin/env python3

"""
test.modtest_d.baseconv: Base conversion unit test for the MMGen suite
"""

from mmgen.util import msg, msg_r

from ..include.common import cfg, qmsg, qmsg_r, vmsg, vmsg_r

class unit_test:

	vectors = {
		'b58': (
			(('00', None),       '1'),
			(('00', 1),          '1'),
			(('00', 2),          '11'),
			(('01', None),       '2'),
			(('01', 1),          '2'),
			(('01', 2),          '12'),
			(('0f', None),       'G'),
			(('0f', 1),          'G'),
			(('0f', 2),          '1G'),
			(('deadbeef', None), '6h8cQN'),
			(('deadbeef', 20),   '111111111111116h8cQN'),
			(('00000000', None), '1'),
			(('00000000', 20),   '11111111111111111111'),
			(('ffffffff', None), '7YXq9G'),
			(('ffffffff', 20),   '111111111111117YXq9G'),
			(('ff'*16, 'seed'),  'YcVfxkQb6JRzqk5kF2tNLv'),
			(('ff'*24, 'seed'),  'QLbz7JHiBTspS962RLKV8GndWFwiEaqKL'),
			(('ff'*32, 'seed'),  'JEKNVnkbo3jma5nREBBJCDoXFVeKkD56V3xKrvRmWxFG'),
			(('00'*16, 'seed'),  '1111111111111111111111'),
			(('00'*24, 'seed'),  '111111111111111111111111111111111'),
			(('00'*32, 'seed'),  '11111111111111111111111111111111111111111111'),
		),
		# MMGen-flavored base32 using simple base conversion
		'b32': (
			(('00', None),       'A'),
			(('00', 1),          'A'),
			(('00', 2),          'AA'),
			(('01', None),       'B'),
			(('01', 1),          'B'),
			(('01', 2),          'AB'),
			(('0f', None),       'P'),
			(('0f', 1),          'P'),
			(('0f', 2),          'AP'),
			(('deadbeef', None), 'DPK3PXP'),
			(('deadbeef', 20),   'AAAAAAAAAAAAADPK3PXP'),
			(('00000000', None), 'A'),
			(('00000000', 20),   'AAAAAAAAAAAAAAAAAAAA'),
			(('ffffffff', None), 'D777777'),
			(('ffffffff', 20),   'AAAAAAAAAAAAAD777777'),
		),
		'b16': (
			(('00', None),       '0'),
			(('00', 1),          '0'),
			(('00', 2),          '00'),
			(('01', None),       '1'),
			(('01', 1),          '1'),
			(('01', 2),          '01'),
			(('0f', None),       'f'),
			(('0f', 1),          'f'),
			(('0f', 2),          '0f'),
			(('deadbeef', None), 'deadbeef'),
			(('deadbeef', 20),   '000000000000deadbeef'),
			(('00000000', None), '0'),
			(('00000000', 20),   '00000000000000000000'),
			(('ffffffff', None), 'ffffffff'),
			(('ffffffff', 20),   '000000000000ffffffff'),
		),
		'b10': (
			(('00', None),       '0'),
			(('00', 1),          '0'),
			(('00', 2),          '00'),
			(('01', None),       '1'),
			(('01', 1),          '1'),
			(('01', 2),          '01'),
			(('0f', None),       '15'),
			(('0f', 1),          '15'),
			(('0f', 2),          '15'),
			(('deadbeef', None), '3735928559'),
			(('deadbeef', 20),   '00000000003735928559'),
			(('00000000', None), '0'),
			(('00000000', 20),   '00000000000000000000'),
			(('ffffffff', None), '4294967295'),
			(('ffffffff', 20),   '00000000004294967295'),
		),
		'b8': (
			(('00', None),       '0'),
			(('00', 1),          '0'),
			(('00', 2),          '00'),
			(('01', None),       '1'),
			(('01', 1),          '1'),
			(('01', 2),          '01'),
			(('0f', None),       '17'),
			(('0f', 1),          '17'),
			(('0f', 2),          '17'),
			(('deadbeef', None), '33653337357'),
			(('deadbeef', 20),   '00000000033653337357'),
			(('00000000', None), '0'),
			(('00000000', 20),   '00000000000000000000'),
			(('ffffffff', None), '37777777777'),
			(('ffffffff', 20),   '00000000037777777777'),
		),
		'b6d': (
			(('00', None),       '1'),
			(('00', 1),          '1'),
			(('00', 2),          '11'),
			(('01', None),       '2'),
			(('01', 1),          '2'),
			(('01', 2),          '12'),
			(('0f', None),       '34'),
			(('0f', 1),          '34'),
			(('0f', 2),          '34'),
			(('010f', None),     '2242'),
			(('010f', 20),       '11111111111111112242'),
			(('deadbeef', None), '2525524636426'),
			(('deadbeef', 20),   '11111112525524636426'),
			(('00000000', None), '1'),
			(('00000000', 20),   '11111111111111111111'),
			(('ffffffff', None), '2661215126614'),
			(('ffffffff', 20),   '11111112661215126614'),

			(('ff'*16, 'seed'),  '34164464641266661652465154654653354436664555521414'),
			(('ff'*24, 'seed'),  '246111411433323364222465566552324652566121541623426135163525451613554313654'),
			(('ff'*32, 'seed'),  '2132521653312613134145131423465414636252114131225324246311141642456513416322412146151432142242565134'),
			(('00'*16, 'seed'),  '1'*50),
			(('00'*24, 'seed'),  '1'*75),
			(('00'*32, 'seed'),  '1'*100),
		),
		'mmgen': (
			(
				('deadbeefdeadbeefdeadbeefdeadbeef', 'seed'),
				'table cast forgive master funny gaze sadness ripple million paint moral match'
			), (
				('deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef', 'seed'),
				'swirl maybe anymore mix scale stray fog use approach page crime rhyme ' +
				'class former strange window snap soon'
			), (
				('deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef', 'seed'),
				'swell type milk figure cheese phone fill black test bloom heard comfort ' +
				'image terrible radio lesson own reply battle goal goodbye need laugh stream'
			), (
				('ffffffffffffffffffffffffffffffff', 'seed'),
				'yellow yeah show bowl season spider cling defeat poison law shelter reflect'
			), (
				('ffffffffffffffffffffffffffffffffffffffffffffffff', 'seed'),
				'yeah youth quit fail perhaps drum out person young click skin ' +
				'weird inside silently perfectly together anyone memory'
			), (
				('ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff', 'seed'),
				'wrote affection object cell opinion here laughter stare honest north cost begin ' +
				'murder something yourself effort acid dot doubt game broke tell guilt innocent'
			), (
				('00000000000000000000000000000001', 'seed'),
				'able ' * 11 + 'about'
			), (
				('000000000000000000000000000000000000000000000001', 'seed'),
				'able ' * 17 + 'about'
			), (
				('0000000000000000000000000000000000000000000000000000000000000001', 'seed'),
				'able ' * 23 + 'about'
			),
		),
	}

	def run_test(self, name, ut):

		msg_r('Testing base conversion routines...')

		from mmgen.baseconv import baseconv
		perr = "length of {!r} less than pad length ({})"
		rerr = "return value ({!r}) does not match reference value ({!r})"

		qmsg_r('\nChecking hex-to-base conversion:')
		for base, data in self.vectors.items():
			fs = "  {h:%s}  {p:<6} {r}" % max(len(d[0][0]) for d in data)
			if not cfg.verbose:
				qmsg_r(f' {base}')
			vmsg(f'\nBase: {base}')
			vmsg(fs.format(h='Input', p='Pad', r='Output'))
			for (hexstr, pad), ret_chk in data:
				ret = baseconv(base).fromhex(hexstr, pad=pad, tostr=True)
				if pad != 'seed':
					assert len(ret) >= (pad or 0), perr.format(ret, pad or 0)
				assert ret == ret_chk, rerr.format(ret, ret_chk)
				vmsg(fs.format(h=hexstr, r=ret, p=str(pad)))

		qmsg_r('\nChecking base-to-hex conversion:')
		for base, data in self.vectors.items():
			fs = "  {h:%s}  {p:<6} {r}" % max(len(d[1]) for d in data)
			if not cfg.verbose:
				qmsg_r(f' {base}')
			vmsg(f'\nBase: {base}')
			vmsg(fs.format(h='Input', p='Pad', r='Output'))
			for (hexstr, pad), ret_chk in data:
				if type(pad) is int:
					pad = len(hexstr)
				ret = baseconv(base).tohex(ret_chk.split() if base == 'mmgen' else ret_chk, pad=pad)
				if pad is None:
					assert int(ret, 16) == int(hexstr, 16), rerr.format(int(ret, 16), int(hexstr, 16))
				else:
					assert ret == hexstr, rerr.format(ret, hexstr)
				vmsg(fs.format(h=ret_chk, r=ret, p=str(pad)))

		qmsg_r('\nChecking wordlist checksums:')
		vmsg('')

		for wl_id in baseconv.constants['wl_chksum']:
			vmsg_r(f'  {wl_id+":":9}')
			baseconv(wl_id).check_wordlist(cfg)

		qmsg('')

		qmsg('Checking error handling:')

		bad_b58 = 'I'*22
		bad_b58len = 'a'*23

		fr58 = baseconv('b58').fromhex
		to58 = baseconv('b58').tohex
		to32 = baseconv('b32').tohex
		to8  = baseconv('b8').tohex

		hse = 'HexadecimalStringError'
		bce = 'BaseConversionError'
		bpe = 'BaseConversionPadError'
		sle = 'SeedLengthError'

		bad_data = (
			('hexstr',           hse, ': not a hexadecimal str', lambda: fr58('x')),
			('hexstr (seed)',    hse, 'seed data not a hexadec', lambda: fr58('x', pad='seed')),
			('hexstr (empty)',   bce, 'empty data not allowed',  lambda: fr58('')),
			('b58 data',         bce, ': not in base58',         lambda: to58('IfFzZ')),
			('b58 data (seed)',  bce, 'seed data not in base58', lambda: to58(bad_b58, pad='seed')),
			('b58 len (seed)',   bce, 'invalid length for',      lambda: to58(bad_b58len, pad='seed')),
			('b58 data (empty)', bce, 'empty base58 data',       lambda: to58('')),
			('b8 data (empty)' , bce, 'empty base8 string data', lambda: to8('')),
			('b32 data',         bce, 'not in MMGen base32',     lambda: to32('1az')),
			('pad arg (in)',     bpe, "illegal value for 'pad'", lambda: fr58('ff', pad='foo')),
			('pad arg (in)',     bpe, "illegal value for 'pad'", lambda: fr58('ff', pad=False)),
			('pad arg (in)',     bpe, "illegal value for 'pad'", lambda: fr58('ff', pad=True)),
			('seedlen (in)',     sle, 'invalid byte length',     lambda: fr58('ff', pad='seed')),
			('pad arg (out)',    bpe, "illegal value for 'pad'", lambda: to58('Z', pad='foo')),
			('pad arg (out)',    bpe, "illegal value for 'pad'", lambda: to58('Z', pad=False)),
			('pad arg (out)',    bpe, "illegal value for 'pad'", lambda: to58('Z', pad=True)),
			('seedlen (out)',    bce, 'invalid length for seed', lambda: to58('Z', pad='seed')),
		)

		ut.process_bad_data(bad_data)

		msg('OK')

		return True

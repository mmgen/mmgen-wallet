#!/usr/bin/env python3
"""
test/unit_tests_d/ut_baseconv.py: Base conversion unit test for the MMGen suite
"""

from mmgen.common import *
from mmgen.exception import *

class unit_test(object):

	vectors = {
		'xmrseed': (
			# 42nsXK8WbVGTNayQ6Kjw5UdgqbQY5KCCufdxdCgF7NgTfjC69Mna7DJSYyie77hZTQ8H92G2HwgFhgEUYnDzrnLnQdF28r3
			(('0000000000000000000000000000000000000000000000000000000000000001','seed'), # 0x1
			'abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey bamboo jaws jerseys abbey'),

			# 49voQEbjouUQSDikRWKUt1PGbS47TBde4hiGyftN46CvTDd8LXCaimjHRGtofCJwY5Ed5QhYwc12P15AH5w7SxUAMCz1nr1
			(('1c95988d7431ecd670cf7d73f45befc6feffffffffffffffffffffffffffff0f','seed'), # 0xffffffff * 8
			'powder directed sayings enmity bacon vapidly entrance bumper noodles iguana sleepless nasty flying soil software foamy solved soggy foamy solved soggy jury yawning ankle solved'),

			# 41i7saPWA53EoHenmJVRt34dubPxsXwoWMnw8AdMyx4mTD1svf7qYzcVjxxRfteLNdYrAxWUMmiPegFW9EfoNgXx7vDMExv
			(('e8164dda6d42bd1e261a3406b2038dcbddadbeefdeadbeefdeadbeefdeadbe0f','seed'), # 0xdeadbeef * 8
			'viewpoint donuts ardent template unveil agile meant unafraid urgent athlete rustled mime azure jaded hawk baby jagged haystack baby jagged haystack ramped oncoming point template'),

			# 42ey1afDFnn4886T7196doS9GPMzexD9gXpsZJDwVjeRVdFCSoHnv7KPbBeGpzJBzHRCAs9UxqeoyFQMYbqSWYTfJJQAWDm
			(('148d78d2aba7dbca5cd8f6abcfb0b3c009ffbdbea1ff373d50ed94d78286640e','seed'), # Monero repo
			'velvet lymph giddy number token physics poetry unquoted nibs useful sabotage limits benches lifestyle eden nitrogen anvil fewest avoid batch vials washing fences goat unquoted'),
		),
		'b58': (
			(('00',None),'1'),
			(('00',1),'1'),
			(('00',2),'11'),
			(('01',None),'2'),
			(('01',1),'2'),
			(('01',2),'12'),
			(('0f',None),'G'),
			(('0f',1),'G'),
			(('0f',2),'1G'),
			(('deadbeef',None),'6h8cQN'),
			(('deadbeef',20),'111111111111116h8cQN'),
			(('00000000',None),'1'),
			(('00000000',20),'11111111111111111111'),
			(('ffffffff',None),'7YXq9G'),
			(('ffffffff',20),'111111111111117YXq9G'),
			(('ff'*16,'seed'),'YcVfxkQb6JRzqk5kF2tNLv'),
			(('ff'*24,'seed'),'QLbz7JHiBTspS962RLKV8GndWFwiEaqKL'),
			(('ff'*32,'seed'),'JEKNVnkbo3jma5nREBBJCDoXFVeKkD56V3xKrvRmWxFG'),
			(('00'*16,'seed'),'1111111111111111111111'),
			(('00'*24,'seed'),'111111111111111111111111111111111'),
			(('00'*32,'seed'),'11111111111111111111111111111111111111111111'),
		),
		# MMGen-flavored base32 using simple base conversion
		'b32': (
			(('00',None),'A'),
			(('00',1),'A'),
			(('00',2),'AA'),
			(('01',None),'B'),
			(('01',1),'B'),
			(('01',2),'AB'),
			(('0f',None),'P'),
			(('0f',1),'P'),
			(('0f',2),'AP'),
			(('deadbeef',None),'DPK3PXP'),
			(('deadbeef',20),'AAAAAAAAAAAAADPK3PXP'),
			(('00000000',None),'A'),
			(('00000000',20),'AAAAAAAAAAAAAAAAAAAA'),
			(('ffffffff',None),'D777777'),
			(('ffffffff',20),'AAAAAAAAAAAAAD777777'),
		),
		'b16': (
			(('00',None),'0'),
			(('00',1),'0'),
			(('00',2),'00'),
			(('01',None),'1'),
			(('01',1),'1'),
			(('01',2),'01'),
			(('0f',None),'f'),
			(('0f',1),'f'),
			(('0f',2),'0f'),
			(('deadbeef',None),'deadbeef'),
			(('deadbeef',20),'000000000000deadbeef'),
			(('00000000',None),'0'),
			(('00000000',20),'00000000000000000000'),
			(('ffffffff',None),'ffffffff'),
			(('ffffffff',20),'000000000000ffffffff'),
		),
		'b10': (
			(('00',None),'0'),
			(('00',1),'0'),
			(('00',2),'00'),
			(('01',None),'1'),
			(('01',1),'1'),
			(('01',2),'01'),
			(('0f',None),'15'),
			(('0f',1),'15'),
			(('0f',2),'15'),
			(('deadbeef',None),'3735928559'),
			(('deadbeef',20),'00000000003735928559'),
			(('00000000',None),'0'),
			(('00000000',20),'00000000000000000000'),
			(('ffffffff',None),'4294967295'),
			(('ffffffff',20),'00000000004294967295'),
		),
		'b8': (
			(('00',None),'0'),
			(('00',1),'0'),
			(('00',2),'00'),
			(('01',None),'1'),
			(('01',1),'1'),
			(('01',2),'01'),
			(('0f',None),'17'),
			(('0f',1),'17'),
			(('0f',2),'17'),
			(('deadbeef',None),'33653337357'),
			(('deadbeef',20),'00000000033653337357'),
			(('00000000',None),'0'),
			(('00000000',20),'00000000000000000000'),
			(('ffffffff',None),'37777777777'),
			(('ffffffff',20),'00000000037777777777'),
		),
		'b6d': (
			(('00',None),'1'),
			(('00',1),'1'),
			(('00',2),'11'),
			(('01',None),'2'),
			(('01',1),'2'),
			(('01',2),'12'),
			(('0f',None),'34'),
			(('0f',1),'34'),
			(('0f',2),'34'),
			(('010f',None),'2242'),
			(('010f',20),'11111111111111112242'),
			(('deadbeef',None),'2525524636426'),
			(('deadbeef',20),'11111112525524636426'),
			(('00000000',None),'1'),
			(('00000000',20),'11111111111111111111'),
			(('ffffffff',None),'2661215126614'),
			(('ffffffff',20),'11111112661215126614'),

			(('ff'*16,'seed'),'34164464641266661652465154654653354436664555521414'),
			(('ff'*24,'seed'),'246111411433323364222465566552324652566121541623426135163525451613554313654'),
			(('ff'*32,'seed'),'2132521653312613134145131423465414636252114131225324246311141642456513416322412146151432142242565134'),
			(('00'*16,'seed'),'1'*50),
			(('00'*24,'seed'),'1'*75),
			(('00'*32,'seed'),'1'*100),
		),
	}

	def run_test(self,name,ut):

		msg_r('Testing base conversion routines...')

		from mmgen.baseconv import baseconv
		perr = "length of {!r} less than pad length ({})"
		rerr = "return value ({!r}) does not match reference value ({!r})"

		qmsg_r('\nChecking hex-to-base conversion:')
		for base,data in self.vectors.items():
			fs = "  {h:%s}  {p:<6} {r}" % max(len(d[0][0]) for d in data)
			if not opt.verbose:
				qmsg_r(f' {base}')
			vmsg(f'\nBase: {base}')
			vmsg(fs.format(h='Input',p='Pad',r='Output'))
			for (hexstr,pad),ret_chk in data:
				ret = baseconv.fromhex(hexstr,wl_id=base,pad=pad,tostr=True)
				if pad != 'seed':
					assert len(ret) >= (pad or 0), perr.format(ret,pad or 0)
				assert ret == ret_chk, rerr.format(ret,ret_chk)
				vmsg(fs.format(h=hexstr,r=ret,p=str(pad)))
#				msg("(('{h}',{p}),'{r}'),".format(h=hexstr,r=ret,c=ret_chk,p=pad))
#			msg('')
#		return True
		qmsg_r('\nChecking base-to-hex conversion:')
		for base,data in self.vectors.items():
			fs = "  {h:%s}  {p:<6} {r}" % max(len(d[1]) for d in data)
			if not opt.verbose:
				qmsg_r(f' {base}')
			vmsg(f'\nBase: {base}')
			vmsg(fs.format(h='Input',p='Pad',r='Output'))
			for (hexstr,pad),ret_chk in data:
				if type(pad) == int:
					pad = len(hexstr)
				ret = baseconv.tohex(
					ret_chk.split() if base == 'xmrseed' else ret_chk,
					wl_id=base,
					pad=pad)
				if pad == None:
					assert int(ret,16) == int(hexstr,16), rerr.format(int(ret,16),int(hexstr,16))
				else:
					assert ret == hexstr, rerr.format(ret,hexstr)
				vmsg(fs.format(h=ret_chk,r=ret,p=str(pad)))
#				msg("(('{h}',{p}),'{r}'),".format(h=hexstr,r=ret_chk,c=ret_chk,p=pad))

		qmsg('')

		vmsg('')
		qmsg('Checking error handling:')

		bad_b58 = 'I'*22
		bad_b58len = 'a'*23

		th = baseconv.tohex
		fh = baseconv.fromhex
		bad_data = (
('hexstr',          'HexadecimalStringError', ': not a hexadecimal str', lambda:fh('x','b58')),
('hexstr (seed)',   'HexadecimalStringError', 'seed data not a hexadec', lambda:fh('x','b58',pad='seed')),
('hexstr (empty)',  'BaseConversionError',    'empty data not allowed',  lambda:fh('','b58')),
('b58 data',        'BaseConversionError',    ': not in base58',         lambda:th('IfFzZ','b58')),
('b58 data (seed)', 'BaseConversionError',    'seed data not in base58', lambda:th(bad_b58,'b58',pad='seed')),
('b58 len (seed)',  'BaseConversionError',    'invalid length for',      lambda:th(bad_b58len,'b58',pad='seed')),
('b58 data (empty)','BaseConversionError',    'empty base58 data',       lambda:th('','b58')),
('b8 data (empty)' ,'BaseConversionError',    'empty base8 string data', lambda:th('','b8')),
('b32 data',        'BaseConversionError',    'not in MMGen base32',     lambda:th('1az','b32')),
('pad arg (in)',    'BaseConversionPadError', "illegal value for 'pad'", lambda:fh('ff','b58',pad='foo')),
('pad arg (in)',    'BaseConversionPadError', "illegal value for 'pad'", lambda:fh('ff','b58',pad=False)),
('pad arg (in)',    'BaseConversionPadError', "illegal value for 'pad'", lambda:fh('ff','b58',pad=True)),
('seedlen (in)',    'SeedLengthError',        'invalid byte length',     lambda:fh('ff','b58',pad='seed')),
('pad arg (out)',   'BaseConversionPadError', "illegal value for 'pad'", lambda:th('Z','b58',pad='foo')),
('pad arg (out)',   'BaseConversionPadError', "illegal value for 'pad'", lambda:th('Z','b58',pad=False)),
('pad arg (out)',   'BaseConversionPadError', "illegal value for 'pad'", lambda:th('Z','b58',pad=True)),
('seedlen (out)',   'BaseConversionError',    'invalid length for seed', lambda:th('Z','b58',pad='seed')),
		)

		ut.process_bad_data(bad_data)

		msg('OK')

		return True

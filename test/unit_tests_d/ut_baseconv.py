#!/usr/bin/env python3
"""
test/unit_tests_d/ut_baseconv.py: Base conversion unit test for the MMGen suite
"""

from mmgen.common import *
from mmgen.exception import *

class unit_test(object):

	vectors = {
		'b58': (
			(('00',None),''),
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
			(('00000000',None),''),
			(('00000000',20),'11111111111111111111'),
			(('ffffffff',None),'7YXq9G'),
			(('ffffffff',20),'111111111111117YXq9G'),
		),
		# MMGen-flavored base32 using simple base conversion
		'b32': (
			(('00',None),''),
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
			(('00000000',None),''),
			(('00000000',20),'AAAAAAAAAAAAAAAAAAAA'),
			(('ffffffff',None),'D777777'),
			(('ffffffff',20),'AAAAAAAAAAAAAD777777'),
		),
		'b16': (
			(('00',None),''),
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
			(('00000000',None),''),
			(('00000000',20),'00000000000000000000'),
			(('ffffffff',None),'ffffffff'),
			(('ffffffff',20),'000000000000ffffffff'),
		),
		'b10': (
			(('00',None),''),
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
			(('00000000',None),''),
			(('00000000',20),'00000000000000000000'),
			(('ffffffff',None),'4294967295'),
			(('ffffffff',20),'00000000004294967295'),
		),
		'b8': (
			(('00',None),''),
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
			(('00000000',None),''),
			(('00000000',20),'00000000000000000000'),
			(('ffffffff',None),'37777777777'),
			(('ffffffff',20),'00000000037777777777'),
		),
	}

	def run_test(self,name):

		msg_r('Testing base conversion routines...')

		from mmgen.util import baseconv
		perr = "length of {!r} less than pad length ({})"
		rerr = "return value ({!r}) does not match reference value ({!r})"

		qmsg_r('\nChecking hex-to-base conversion:')
		fs = "  {h:10} {p:6} {r}"
		for base,data in self.vectors.items():
			if not opt.verbose: qmsg_r(' {}'.format(base))
			vmsg('\nBase: {}'.format(base))
			vmsg(fs.format(h='Input',p='Pad',r='Output'))
			for (hexstr,pad),ret_chk in data:
				ret = baseconv.fromhex(hexstr,wl_id=base,pad=pad,tostr=True)
				assert len(ret) >= (pad or 0), perr.format(ret,pad)
				assert ret == ret_chk, rerr.format(ret,ret_chk)
				vmsg(fs.format(h=hexstr,r=ret,p=str(pad)))
#				msg("(('{h}',{p}),'{r}'),".format(h=hexstr,r=ret,c=ret_chk,p=pad))
#			msg('')
#		return True
		qmsg_r('\nChecking base-to-hex conversion:')
		fs = "  {h:24} {p:<6} {r}"
		for base,data in self.vectors.items():
			if not opt.verbose: qmsg_r(' {}'.format(base))
			vmsg('\nBase: {}'.format(base))
			vmsg(fs.format(h='Input',p='Pad',r='Output'))
			for (hexstr,pad),ret_chk in data:
				ret = baseconv.tohex(ret_chk,wl_id=base,pad=len(hexstr))
				assert ret == hexstr, rerr.format(ret,ret_chk)
				vmsg(fs.format(h=ret_chk,r=ret,p=len(hexstr)))
#				msg("(('{h}',{p}),'{r}'),".format(h=hexstr,r=ret_chk,c=ret_chk,p=pad))

		qmsg('')
		msg('OK')

		return True

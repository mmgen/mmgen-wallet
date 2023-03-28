#!/usr/bin/env python3

from mmgen.common import *

cfg = opts.init()

from mmgen.util import msg

text = {
	'gr': 'Greek text: {}'.format(''.join(map(chr,list(range(913,939))))),
	'ru': 'Russian text: {}'.format(''.join(map(chr,list(range(1040,1072))))),
	'zh': 'Chinese text: {}'.format('所以，我們非常需要這樣一種電子支付系統，它基於密碼學原理而不基於信用，'),
	'jp': 'Japanese text: {}'.format('必要なのは、信用ではなく暗号化された証明に基づく電子取引システムであり、')
}

if not cfg._args or not cfg._args[0] in text:
	die(2,'argument must be one of {}'.format(list(text.keys())))

msg(text[cfg._args[0]])

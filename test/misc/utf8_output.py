#!/usr/bin/env python3

text = {
	'gr': 'Greek text: {}'.format(''.join(map(chr, list(range(913, 939))))),
	'ru': 'Russian text: {}'.format(''.join(map(chr, list(range(1040, 1072))))),
	'zh': 'Chinese text: {}'.format('所以，我們非常需要這樣一種電子支付系統，它基於密碼學原理而不基於信用，'),
	'jp': 'Japanese text: {}'.format('必要なのは、信用ではなく暗号化された証明に基づく電子取引システムであり、')
}

import sys
from mmgen.util import msg, die

if len(sys.argv) != 2 or not sys.argv[1] in text:
	die(2, f'argument must be one of {list(text.keys())}')

msg(text[sys.argv[1]])

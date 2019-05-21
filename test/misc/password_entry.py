#!/usr/bin/env python3

from mmgen.util import msg
from mmgen.common import *

cmd_args = opts.init({'text': { 'desc': '', 'usage':'', 'options':'-e, --echo-passphrase foo' }})

p = ('Enter passphrase: ','Enter passphrase (echoed): ')[bool(opt.echo_passphrase)]

pw = get_words_from_user(p)
msg('Entered: {}'.format(' '.join(pw)))
#msg(ascii(pw))

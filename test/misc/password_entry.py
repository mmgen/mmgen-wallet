#!/usr/bin/env python3

import sys,os
pn = os.path.abspath(os.path.dirname(sys.argv[0]))
parpar = os.path.dirname(os.path.dirname(pn))
os.chdir(parpar)
sys.path[0] = os.curdir

from mmgen.util import msg
from mmgen.common import *

cmd_args = opts.init({'text': { 'desc': '', 'usage':'', 'options':'-e, --echo-passphrase foo' }})

p = ('Enter passphrase: ','Enter passphrase (echoed): ')[bool(opt.echo_passphrase)]

pw = get_words_from_user(p)
msg('Entered: {}'.format(' '.join(pw)))

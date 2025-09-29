#!/usr/bin/env python3

import sys, os, atexit
pn = os.path.abspath(os.path.dirname(sys.argv[0]))
parpar = os.path.dirname(os.path.dirname(pn))
os.chdir(parpar)
sys.path[0] = os.curdir

from mmgen.cfg import Config
from mmgen.util import msg
from mmgen.ui import keypress_confirm
from mmgen.led import LEDControl

opts_data = {
	'text': {
		'desc': 'Interactively test LED functionality',
		'usage': 'command',
		'options': """
-h, --help     Print this help message
""",
	}
}

cfg = Config(opts_data=opts_data)

def confirm_or_exit(prompt):
	keypress_confirm(cfg, f'{prompt}.  OK?', default_yes=True, do_exit=True)

confirm_or_exit('This script will interactively test LED functionality')

led = LEDControl(enabled=True)

color = led.board.color.capitalize()

atexit.register(led.stop)

confirm_or_exit(f'{color} LED should now be turned off')

led.set('busy')

confirm_or_exit(f'{color} LED should now be signaling busy (rapid flashing)')

led.set('standby')

confirm_or_exit(f'{color} LED should now be signaling standby (slow flashing)')

led.set('error')

confirm_or_exit(f'{color} LED should now be signaling error (insistent flashing)')

led.set('off')

confirm_or_exit(f'{color} LED should now be turned off')

led.stop()

confirm_or_exit(f'{color} LED should now be in its original state [trigger={led.orig_trigger_state}]')

from .led_orig import *

class overlay_fake_LEDControl:
	boards = {
		'dummy': LEDControl.binfo(
			name    = 'Dummy Testing Board',
			control = 'test/tmp/led_status',
			trigger = 'test/tmp/led_trigger')}

LEDControl.boards.update(overlay_fake_LEDControl.boards)

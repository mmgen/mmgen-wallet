from .__init___orig import *

class overlay_fake_Autosign:

	def init_fixup(self):
		if self.cfg.test_suite_autosign_root_dir and self.mountpoint.anchor:
			root_dir = os.path.join(
				self.cfg.test_suite_autosign_root_dir,
				'online' if self.cfg.online else 'offline')
			for k in ('mountpoint', 'shm_dir', 'wallet_dir'):
				setattr(self, k, Path(root_dir + str(getattr(self, k))))
			# mount --type=fuse-ext2 --options=rw+ ### current fuse-ext2 (0.4 29) is buggy - can’t use
			if sys.platform == 'linux':
				self.dev_label = 'MMGEN_TS_ONLINE' if self.cfg.online else 'MMGEN_TS_OFFLINE'
				self.mount_cmd  = f'sudo mount LABEL={self.dev_label} {self.mountpoint}'
				self.umount_cmd = f'sudo umount {self.mountpoint}'

Autosign.dev_label          = 'MMGEN_TS_TX' # autosign_live only (Linux)
Autosign.linux_mount_subdir = 'mmgen_ts_autosign'
Autosign.linux_blkid_cmd    = 'sudo blkid -s LABEL -o value'
Autosign.macOS_ramdisk_name = 'TestAutosignRamDisk'
Autosign.init_fixup         = overlay_fake_Autosign.init_fixup

if os.getenv('MMGEN_TEST_SUITE_AUTOSIGN_LED_SIMULATE'):
	Autosign.simulate_led = True

from .autosign_orig import *

class overlay_fake_Autosign:

	def init_fixup(self):
		if pfx := self.cfg.test_suite_root_pfx:
			subdir = pfx + '/' + ('online' if self.cfg.online else 'offline')
			for k in ('mountpoint', 'shm_dir', 'wallet_dir'):
				orig_path = str(getattr(self, k))
				setattr(self, k, Path(subdir + orig_path.removeprefix(subdir)))
			# mount --type=fuse-ext2 --options=rw+ ### current fuse-ext2 (0.4 29) is buggy - can’t use
			import sys
			if sys.platform == 'linux':
				self.dev_label = 'MMGEN_TS_ONLINE' if self.cfg.online else 'MMGEN_TS_OFFLINE'
				self.mount_cmd  = f'sudo mount LABEL={self.dev_label} {self.mountpoint}'
				self.umount_cmd = f'sudo umount {self.mountpoint}'
				self.linux_blkid_cmd = 'sudo blkid -s LABEL -o value'

Autosign.dev_label          = 'MMGEN_TS_TX' # autosign_live only (Linux)
Autosign.linux_mount_subdir = 'mmgen_ts_autosign'
Autosign.macOS_ramdisk_name = 'TestAutosignRamDisk'
Autosign.init_fixup         = overlay_fake_Autosign.init_fixup

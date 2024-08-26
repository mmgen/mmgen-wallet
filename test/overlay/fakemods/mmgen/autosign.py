from .autosign_orig import *

class overlay_fake_Autosign:

	def init_fixup(self):
		if pfx := self.cfg.test_suite_root_pfx:
			subdir = pfx + '/' + ('online' if self.cfg.online else 'offline')
			for k in ('mountpoint', 'shm_dir', 'wallet_dir', 'dev_label_dir'):
				if hasattr(self, k):
					orig_path = str(getattr(self, k))
					setattr(self, k, Path(subdir + orig_path.removeprefix(subdir)))
			# mount --type=fuse-ext2 --options=rw+ ### current fuse-ext2 (0.4 29) is buggy - can’t use
			self.fs_image_path = Path(f'{pfx}/removable_device_image').absolute()
			import sys
			if sys.platform == 'linux':
				self.mount_cmd  = f'sudo mount {self.fs_image_path} {self.mountpoint}'
				self.umount_cmd = f'sudo umount {self.mountpoint}'

Autosign.dev_label          = 'MMGEN_TS_TX'
Autosign.linux_mount_subdir = 'mmgen_ts_autosign'
Autosign.init_fixup         = overlay_fake_Autosign.init_fixup

from .autosign_orig import *

class overlay_fake_Autosign:

	def init_cfg(self):
		if pfx := self.cfg.test_suite_root_pfx:
			subdir = 'online' if self.cfg.online else 'offline'
			self.mountpoint     = Path(f'{pfx}/{subdir}/{self.dfl_mountpoint}')
			self.wallet_dir     = Path(f'{pfx}/{subdir}/{self.dfl_wallet_dir}')
			self.dev_label_path = Path(f'{pfx}/{subdir}/{self.dfl_dev_label_dir}') / self.dev_label
			# mount --type=fuse-ext2 --options=rw+ ### current fuse-ext2 (0.4 29) is buggy - can’t use
			self.fs_image_path  = Path(f'{pfx}/removable_device_image')
			self.mount_cmd      = f'sudo mount {self.fs_image_path}'
			self.umount_cmd     = 'sudo umount'
		else:
			self.init_cfg_orig()

Autosign.init_cfg_orig = Autosign.init_cfg
Autosign.init_cfg      = overlay_fake_Autosign.init_cfg

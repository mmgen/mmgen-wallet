import sys,os,shutil

def get_overlay_dir(repo_root):
	return os.path.join(repo_root,'test','overlay','tree')

def overlay_setup(repo_root):

	def process_srcdir(d):
		srcdir = os.path.join(repo_root,*d.split('.'))
		destdir = os.path.join(overlay_dir,*d.split('.'))
		os.makedirs(destdir)
		for fn in os.listdir(srcdir):
			if (
				fn.endswith('.py') or
				d == 'mmgen.data' or
				d == 'mmgen' and fn.startswith('secp256k1')
			):
				if d == 'mmgen' and fn in fakemods:
					make_link(
						os.path.join(fakemod_dir,fn),
						os.path.join(destdir,fn) )
#					link_fn = fn.removesuffix('.py') + '_orig.py' # Python 3.9
					link_fn = fn[:-3] + '_orig.py'
				else:
					link_fn = fn
				make_link(
					os.path.join(srcdir,fn),
					os.path.join(destdir,link_fn) )

	overlay_dir = get_overlay_dir(repo_root)
	fakemod_dir = os.path.join(repo_root,'test','overlay','fakemods')
	fakemods  = os.listdir(fakemod_dir)
	make_link = os.symlink if sys.platform == 'linux' else shutil.copy2

	if not os.path.exists(os.path.join(overlay_dir,'mmgen','main.py')):
		sys.stderr.write('Setting up overlay tree\n')
		shutil.rmtree(overlay_dir,ignore_errors=True)
		for d in (
				'mmgen',
				'mmgen.data',
				'mmgen.share',
				'mmgen.tool',
				'mmgen.proto',
				'mmgen.base_proto',
				'mmgen.base_proto.ethereum',
				'mmgen.base_proto.ethereum.pyethereum',
				'mmgen.base_proto.ethereum.rlp',
				'mmgen.base_proto.ethereum.rlp.sedes' ):
			process_srcdir(d)

	return overlay_dir

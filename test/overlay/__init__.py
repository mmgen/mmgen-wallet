import sys,os,shutil

def get_overlay_tree_dir(repo_root):
	return os.path.join(repo_root,'test','overlay','tree')

def overlay_setup(repo_root):

	def process_srcdir(d):
		relpath = d.split('.')
		srcdir = os.path.join(repo_root,*relpath)
		destdir = os.path.join(overlay_tree_dir,*relpath)
		fakemod_dir = os.path.join(fakemod_root,*(relpath[1:]))
		os.makedirs(destdir)
		for fn in os.listdir(srcdir):
			if (
				fn.endswith('.py') or
				d == 'mmgen.data' or
				d == 'mmgen.proto.secp256k1' and fn.startswith('secp256k1')
			):
				if os.path.exists(os.path.join(fakemod_dir,fn)):
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

	overlay_tree_dir = get_overlay_tree_dir(repo_root)

	if not os.path.exists(os.path.join(overlay_tree_dir,'mmgen','main.py')):
		fakemod_root = os.path.join(repo_root,'test','overlay','fakemods')
		make_link = os.symlink if sys.platform == 'linux' else shutil.copy2
		sys.stderr.write('Setting up overlay tree\n')
		shutil.rmtree(overlay_tree_dir,ignore_errors=True)
		for d in (
				'mmgen',
				'mmgen.contrib',
				'mmgen.data',
				'mmgen.proto',
				'mmgen.proto.bch',
				'mmgen.proto.btc',
				'mmgen.proto.btc.tx',
				'mmgen.proto.btc.tw',
				'mmgen.proto.etc',
				'mmgen.proto.eth',
				'mmgen.proto.eth.pyethereum',
				'mmgen.proto.eth.rlp',
				'mmgen.proto.eth.rlp.sedes',
				'mmgen.proto.eth.tx',
				'mmgen.proto.eth.tw',
				'mmgen.proto.ltc',
				'mmgen.proto.secp256k1',
				'mmgen.proto.xmr',
				'mmgen.proto.zec',
				'mmgen.share',
				'mmgen.tool',
				'mmgen.tx',
				'mmgen.tw',
				'mmgen.wallet',
				'mmgen.wordlist' ):
			process_srcdir(d)

	return overlay_tree_dir

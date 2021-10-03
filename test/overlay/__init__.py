import sys,os

def overlay_setup():

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
				if fn in fakemods:
					os.symlink(
						os.path.join(fakemod_dir,fn),
						os.path.join(destdir,fn) )
					link_fn = fn.removesuffix('.py') + '_orig.py'
				else:
					link_fn = fn
				os.symlink(
					os.path.join(srcdir,fn),
					os.path.join(destdir,link_fn) )

	repo_root = os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))
	overlay_dir = os.path.join(repo_root,'test','overlay','tree')
	fakemod_dir = os.path.join(repo_root,'test','overlay','fakemods')
	fakemods  = os.listdir(fakemod_dir)
	if not os.path.exists(os.path.join(overlay_dir,'mmgen','main.py')):
		for d in (
				'mmgen',
				'mmgen.data',
				'mmgen.share',
				'mmgen.altcoins',
				'mmgen.altcoins.eth',
				'mmgen.altcoins.eth.pyethereum',
				'mmgen.altcoins.eth.rlp',
				'mmgen.altcoins.eth.rlp.sedes' ):
			process_srcdir(d)

	return overlay_dir

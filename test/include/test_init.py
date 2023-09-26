import sys,os
os.environ['MMGEN_TEST_SUITE'] = '1'
repo_root = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),os.pardir)))
os.environ['PYTHONPATH'] = repo_root
os.chdir(repo_root)
sys.path[0] = repo_root
from test.overlay import overlay_setup
overlay_setup(repo_root)

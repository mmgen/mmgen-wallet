from .keygen_orig import *

backend_data['std']['backends'] = ('libsecp256k1', 'python-ecdsa')
backend_data['monero']['backends'] = ('nacl', 'ed25519ll-djbec', 'ed25519')

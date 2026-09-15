from .protobuf_orig import *

class overlay_fake_Tx:

	verify_sig_backends = ('secp256k1', 'ecdsa')

	def verify_sig_ecdsa(self, *, sig, msghash, pubkey):
		# ecdsa.keys.VerifyingKey.verify_digest():
		#   raises BadSignatureError if the signature is invalid or malformed
		import ecdsa
		ec_pubkey = ecdsa.VerifyingKey.from_string(pubkey, curve=ecdsa.curves.SECP256k1)
		ec_pubkey.verify_digest(sig, msghash)

Tx.verify_sig_backends = overlay_fake_Tx.verify_sig_backends
Tx.verify_sig_ecdsa = overlay_fake_Tx.verify_sig_ecdsa

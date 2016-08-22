#include <Python.h>
#include <secp256k1.h>

static PyObject * priv2pub(PyObject *self, PyObject *args) {
    const unsigned char * privkey;
    const int klen;
    const int compressed;
    if (!PyArg_ParseTuple(args, "t#I", &privkey, &klen, &compressed))
        return NULL;
    if (klen != 32) return NULL;
    secp256k1_pubkey pubkey;
    size_t pubkeyclen = compressed == 1 ? 33: 65;
    unsigned char pubkeyc[pubkeyclen];
	static secp256k1_context *ctx = NULL;
	if (ctx == NULL) {
	/*	puts ("Initializing context"); */
		ctx = secp256k1_context_create(SECP256K1_CONTEXT_SIGN | SECP256K1_CONTEXT_VERIFY);
	}
    if (secp256k1_ec_pubkey_create(ctx, &pubkey, privkey) != 1) return NULL;
    if (secp256k1_ec_pubkey_serialize(ctx, pubkeyc, &pubkeyclen, &pubkey,
			compressed == 1 ? SECP256K1_EC_COMPRESSED: SECP256K1_EC_UNCOMPRESSED) != 1)
				return NULL;
    return Py_BuildValue("s#", pubkeyc,pubkeyclen);
}

static PyMethodDef secp256k1Methods[] = {
    {"priv2pub", priv2pub, METH_VARARGS, "Generate pubkey from privkey using libsecp256k1"},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

PyMODINIT_FUNC initsecp256k1(void) {
    PyObject *m;
    m = Py_InitModule("secp256k1", secp256k1Methods);
    if (m == NULL) return;
}

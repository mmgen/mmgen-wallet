/*
  mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
  Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>

  This program is free software: you can redistribute it and/or modify it under
  the terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  This program is distributed in the hope that it will be useful, but WITHOUT
  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
  FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
  details.

  You should have received a copy of the GNU General Public License along with
  this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <secp256k1.h>

int privkey_check(
		const secp256k1_context * ctx,
		const unsigned char *     privkey_bytes,
		const Py_ssize_t          privkey_bytes_len,
		const char *              desc
	) {
	if (privkey_bytes_len != 32) {
		char buf[64 + strlen(desc)];
		sprintf(buf, "%s length not 32 bytes", desc);
		PyErr_SetString(PyExc_ValueError, buf);
		return 0;
	}
	if (secp256k1_ec_seckey_verify(ctx, privkey_bytes) != 1) {
		char buf[64 + strlen(desc)];
		sprintf(buf, "%s not in allowable range", desc);
		PyErr_SetString(PyExc_ValueError, buf);
		return 0;
	}
	return 1;
}

static PyObject * pubkey_gen(PyObject *self, PyObject *args) {
	const unsigned char * privkey_bytes;
	const Py_ssize_t privkey_bytes_len;
	const int compressed;
	if (!PyArg_ParseTuple(args, "y#I", &privkey_bytes, &privkey_bytes_len, &compressed)) {
		PyErr_SetString(PyExc_ValueError, "Unable to parse extension mod arguments");
		return NULL;
	}
	size_t pubkey_bytes_len = compressed == 1 ? 33 : 65;
	unsigned char pubkey_bytes[pubkey_bytes_len];
	secp256k1_pubkey pubkey;
	secp256k1_context *ctx = secp256k1_context_create(SECP256K1_CONTEXT_NONE);
	if (ctx == NULL) {
		PyErr_SetString(PyExc_RuntimeError, "Context initialization failed");
		return NULL;
	}
	if (!privkey_check(ctx, privkey_bytes, privkey_bytes_len, "Private key")) {
		return NULL;
	}
	if (secp256k1_ec_pubkey_create(ctx, &pubkey, privkey_bytes) != 1) {
		PyErr_SetString(PyExc_RuntimeError, "Public key creation failed");
		return NULL;
	}
	if (secp256k1_ec_pubkey_serialize(ctx, pubkey_bytes, &pubkey_bytes_len, &pubkey,
			compressed == 1 ? SECP256K1_EC_COMPRESSED : SECP256K1_EC_UNCOMPRESSED) != 1) {
		PyErr_SetString(PyExc_RuntimeError, "Public key serialization failed");
		return NULL;
	}
	return Py_BuildValue("y#", pubkey_bytes, pubkey_bytes_len);
}

/* https://docs.python.org/3/howto/cporting.html */

struct module_state {
    PyObject *error;
};

#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))

static PyMethodDef secp256k1_methods[] = {
	{
		"pubkey_gen",
		pubkey_gen,
		METH_VARARGS,
		"Generate a serialized pubkey from privkey bytes"
	},
    {NULL, NULL}
};

static int secp256k1_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int secp256k1_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "secp256k1",
        NULL,
        sizeof(struct module_state),
        secp256k1_methods,
        NULL,
        secp256k1_traverse,
        secp256k1_clear,
        NULL
};

#define INITERROR return NULL

PyMODINIT_FUNC PyInit_secp256k1(void) {
    PyObject *module = PyModule_Create(&moduledef);

    if (module == NULL)
        INITERROR;
    struct module_state *st = GETSTATE(module);

    st->error = PyErr_NewException("secp256k1.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }
    return module;
}

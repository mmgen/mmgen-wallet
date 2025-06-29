/*
  mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
  Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>

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

/*
   NOTE: deprecated context flags SECP256K1_CONTEXT_SIGN | SECP256K1_CONTEXT_VERIFY
   must be used for now instead of SECP256K1_CONTEXT_NONE (see libsecp256k1 CHANGELOG)
   for backward compatibility with libsecp256k1 <v0.2.0 (i.e. pre-bookworm distros).
*/

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <secp256k1.h>
#include <secp256k1_recovery.h>
#include "random.h"

static secp256k1_context * create_context(
		const unsigned char randomize
	) {
	secp256k1_context *ctx = secp256k1_context_create(
		SECP256K1_CONTEXT_SIGN | SECP256K1_CONTEXT_VERIFY
		/* SECP256K1_CONTEXT_NONE */ /* see NOTE above */
	);
	if (randomize) {
		unsigned char buf[32];
		if (!fill_random(buf, sizeof(buf))) {
			printf("Failed to generate entropy\n");
			return NULL;
		}
		if (!secp256k1_context_randomize(ctx, buf)) {
			printf("Failed to randomize context\n");
			return NULL;
		}
	}
	return ctx;
}

static int privkey_check(
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

static int pubkey_parse_with_check(
		const secp256k1_context * ctx,
		secp256k1_pubkey *        pubkey_ptr,
		const unsigned char *     pubkey_bytes,
		const Py_ssize_t          pubkey_bytes_len
	) {
	if (ctx == NULL) {
		PyErr_SetString(PyExc_RuntimeError, "Context initialization failed");
		return 0;
	}
	if (pubkey_bytes_len == 33) {
		if (pubkey_bytes[0] != 3 && pubkey_bytes[0] != 2) {
			PyErr_SetString(
				PyExc_ValueError,
				"Invalid first byte for serialized compressed public key");
			return 0;
		}
	} else if (pubkey_bytes_len == 65) {
		if (pubkey_bytes[0] != 4) {
			PyErr_SetString(
				PyExc_ValueError,
				"Invalid first byte for serialized uncompressed public key");
			return 0;
		}
	} else {
		PyErr_SetString(PyExc_ValueError, "Serialized public key length not 33 or 65 bytes");
		return 0;
	}
	/* checks for point-at-infinity (via secp256k1_pubkey_save) */
	if (secp256k1_ec_pubkey_parse(ctx, pubkey_ptr, pubkey_bytes, pubkey_bytes_len) != 1) {
		PyErr_SetString(
			PyExc_ValueError,
			"Public key could not be parsed or encodes point-at-infinity");
		return 0;
	}
	return 1;
}

static PyObject * pubkey_gen(PyObject *self, PyObject *args) {
	const unsigned char * privkey_bytes;
	Py_ssize_t privkey_bytes_len;
	int compressed;
	if (!PyArg_ParseTuple(args, "y#i", &privkey_bytes, &privkey_bytes_len, &compressed)) {
		PyErr_SetString(PyExc_ValueError, "Unable to parse extension mod arguments");
		return NULL;
	}
	size_t pubkey_bytes_len = compressed == 1 ? 33 : 65;
	unsigned char pubkey_bytes[pubkey_bytes_len];
	secp256k1_pubkey pubkey;
	secp256k1_context *ctx = create_context(1);
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

static PyObject * pubkey_tweak_add(PyObject *self, PyObject *args) {
	const unsigned char * pubkey_bytes;
	const unsigned char * tweak_bytes;
	Py_ssize_t pubkey_bytes_len;
	Py_ssize_t tweak_bytes_len;
	if (!PyArg_ParseTuple(
			args,
			"y#y#",
			&pubkey_bytes,
			&pubkey_bytes_len,
			&tweak_bytes,
			&tweak_bytes_len)) {
		PyErr_SetString(PyExc_ValueError, "Unable to parse extension mod arguments");
		return NULL;
	}
	secp256k1_context *ctx = create_context(1);
	secp256k1_pubkey pubkey;
	if (!pubkey_parse_with_check(ctx, &pubkey, pubkey_bytes, pubkey_bytes_len)) {
		return NULL;
	}
	if (!privkey_check(ctx, tweak_bytes, tweak_bytes_len, "Tweak")) {
		return NULL;
	}
	/* checks for point-at-infinity (via secp256k1_pubkey_save) */
	if (secp256k1_ec_pubkey_tweak_add(ctx, &pubkey, tweak_bytes) != 1) {
		PyErr_SetString(
			PyExc_RuntimeError,
			"Adding public key points failed or result was point-at-infinity");
		return NULL;
	}
	unsigned char new_pubkey_bytes[pubkey_bytes_len];
	if (secp256k1_ec_pubkey_serialize(
			ctx,
			new_pubkey_bytes,
			(size_t*) &pubkey_bytes_len,
			&pubkey,
			pubkey_bytes_len == 33 ? SECP256K1_EC_COMPRESSED : SECP256K1_EC_UNCOMPRESSED) != 1) {
		PyErr_SetString(PyExc_RuntimeError, "Public key serialization failed");
		return NULL;
	}
	return Py_BuildValue("y#", new_pubkey_bytes, pubkey_bytes_len);
}

static PyObject * pubkey_check(PyObject *self, PyObject *args) {
	const unsigned char * pubkey_bytes;
	Py_ssize_t pubkey_bytes_len;
	if (!PyArg_ParseTuple(args, "y#", &pubkey_bytes, &pubkey_bytes_len)) {
		PyErr_SetString(PyExc_ValueError, "Unable to parse extension mod arguments");
		return NULL;
	}
	secp256k1_context *ctx = create_context(1);
	secp256k1_pubkey pubkey;
	if (!pubkey_parse_with_check(ctx, &pubkey, pubkey_bytes, pubkey_bytes_len)) {
		return NULL;
	}
	return Py_BuildValue("I", 1);
}

/*
 * returns 64-byte serialized signature (r + s) plus integer recovery ID in range 0-3
 */
static PyObject * sign_msghash(PyObject *self, PyObject *args) {

	const unsigned char * msghash_bytes;
	const unsigned char * privkey_bytes;
	Py_ssize_t msghash_bytes_len;
	Py_ssize_t privkey_bytes_len;

	if (!PyArg_ParseTuple(
			args,
			"y#y#",
			&msghash_bytes,
			&msghash_bytes_len,
			&privkey_bytes,
			&privkey_bytes_len)) {
		PyErr_SetString(PyExc_ValueError, "Unable to parse extension mod arguments");
		return NULL;
	}

	if (msghash_bytes_len != 32) {
		PyErr_SetString(PyExc_RuntimeError, "Invalid message hash length (not 32 bytes)");
		return NULL;
	}

	secp256k1_context *ctx = create_context(1);

	if (!privkey_check(ctx, privkey_bytes, privkey_bytes_len, "Private key")) {
		return NULL;
	}

	secp256k1_ecdsa_recoverable_signature rsig;
	unsigned char rsig_serialized[65];
	int recid;

	if (!secp256k1_ecdsa_sign_recoverable(ctx, &rsig, msghash_bytes, privkey_bytes, NULL, NULL)) {
		PyErr_SetString(PyExc_ValueError, "Unable to sign message hash");
		return NULL;
	}
	if (!secp256k1_ecdsa_recoverable_signature_serialize_compact(ctx, rsig_serialized, &recid, &rsig)) {
		PyErr_SetString(PyExc_ValueError, "Unable to serialize signature");
		return NULL;
	}
	/* truncate serialized sig to 64 bytes */
	return Py_BuildValue("y#I", rsig_serialized, 64, recid);
}

static PyObject * verify_sig(PyObject *self, PyObject *args) {

	const unsigned char * sig_bytes;
	const unsigned char * msghash_bytes;
	const unsigned char * pubkey_bytes;
	Py_ssize_t sig_bytes_len;
	Py_ssize_t msghash_bytes_len;
	Py_ssize_t pubkey_bytes_len;

	if (!PyArg_ParseTuple(
			args,
			"y#y#y#",
			&sig_bytes,
			&sig_bytes_len,
			&msghash_bytes,
			&msghash_bytes_len,
			&pubkey_bytes,
			&pubkey_bytes_len)) {
		PyErr_SetString(PyExc_ValueError, "Unable to parse extension mod arguments");
		return NULL;
	}

	if (sig_bytes_len != 64) {
		PyErr_SetString(PyExc_RuntimeError, "Invalid signature length (not 64 bytes)");
		return NULL;
	}
	if (msghash_bytes_len != 32) {
		PyErr_SetString(PyExc_RuntimeError, "Invalid message hash length (not 32 bytes)");
		return NULL;
	}

	secp256k1_ecdsa_signature sig;
	secp256k1_pubkey pubkey;
	secp256k1_context *ctx = create_context(1);

	if (!secp256k1_ecdsa_signature_parse_compact(ctx, &sig, sig_bytes)) {
		PyErr_SetString(PyExc_RuntimeError, "Failed to parse signature");
		return NULL;
	}

	if (!secp256k1_ec_pubkey_parse(ctx, &pubkey, pubkey_bytes, pubkey_bytes_len)) {
		PyErr_SetString(PyExc_RuntimeError, "Failed to parse public key");
		return NULL;
	}

	/* returns 1 on valid sig, 0 on invalid sig */
	return Py_BuildValue("I", secp256k1_ecdsa_verify(ctx, &sig, msghash_bytes, &pubkey));
}

static PyObject * pubkey_recover(PyObject *self, PyObject *args) {

	const unsigned char * msghash_bytes;
	const unsigned char * sig_bytes;
	int recid;
	int compressed;
	Py_ssize_t msghash_bytes_len;
	Py_ssize_t sig_bytes_len;

	if (!PyArg_ParseTuple(
			args,
			"y#y#ii",
			&msghash_bytes,
			&msghash_bytes_len,
			&sig_bytes,
			&sig_bytes_len,
			&recid,
			&compressed)) {
		PyErr_SetString(PyExc_ValueError, "Unable to parse extension mod arguments");
		return NULL;
	}

	if (recid < 0 || recid > 3) {
		PyErr_SetString(PyExc_RuntimeError, "Invalid recovery ID (not in range 0-3)");
		return NULL;
	}
	if (sig_bytes_len != 64) {
		PyErr_SetString(PyExc_RuntimeError, "Invalid signature length (not 64 bytes)");
		return NULL;
	}
	if (msghash_bytes_len != 32) {
		PyErr_SetString(PyExc_RuntimeError, "Invalid message hash length (not 32 bytes)");
		return NULL;
	}

	secp256k1_context *ctx = create_context(1);
	secp256k1_ecdsa_recoverable_signature rsig;
	secp256k1_pubkey pubkey;
	size_t pubkey_bytes_len = compressed == 1 ? 33 : 65;
	unsigned char pubkey_bytes[pubkey_bytes_len];

	if (!secp256k1_ecdsa_recoverable_signature_parse_compact(ctx, &rsig, sig_bytes, recid)) {
		PyErr_SetString(PyExc_RuntimeError, "Failed to parse signature");
		return NULL;
	}
	if (!secp256k1_ecdsa_recover(ctx, &pubkey, &rsig, msghash_bytes)) {
		PyErr_SetString(PyExc_RuntimeError, "Failed to recover public key");
		return NULL;
	}
	if (secp256k1_ec_pubkey_serialize(ctx, pubkey_bytes, &pubkey_bytes_len, &pubkey,
			compressed == 1 ? SECP256K1_EC_COMPRESSED : SECP256K1_EC_UNCOMPRESSED) != 1) {
		PyErr_SetString(PyExc_RuntimeError, "Failed to serialize public key");
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
	{
		"pubkey_tweak_add",
		pubkey_tweak_add,
		METH_VARARGS,
		"Add scalar bytes to a serialized pubkey, returning a serialized pubkey"
	},
	{
		"pubkey_check",
		pubkey_check,
		METH_VARARGS,
		"Check a serialized pubkey, ensuring the encoded point is not point-at-infinity"
	},
	{
		"sign_msghash",
		sign_msghash,
		METH_VARARGS,
		"Sign a 32-byte message hash with a private key"
	},
	{
		"verify_sig",
		verify_sig,
		METH_VARARGS,
		"Verify a signature"
	},
	{
		"pubkey_recover",
		pubkey_recover,
		METH_VARARGS,
		"Recover a serialized pubkey from a recoverable signature plus signed message"
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

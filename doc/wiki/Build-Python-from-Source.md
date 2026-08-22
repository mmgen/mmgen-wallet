Building Python from source takes very little time and effort!  Just follow
these easy steps:

### Clone the source repository

Make a shallow clone at the tip of the desired branch, `3.15` in this example.
To build a specific version, you’d specify a tag instead a branch, e.g.
`--branch=v3.14.7`.

```bash
$ git clone --depth=1 --branch=3.15 https://github.com/python/cpython.git
```

### Configure, compile, and install

In this example, we’ll build a free-threaded interpreter. For a single-threaded
one you’d omit the `--disable-gil` option.

Omitting `--enable-optimizations` will also cause the tests to be skipped and
thus greatly speed up the build, though this not recommended.  Compilation
without the tests typically takes around 10 seconds (!) on a modern 12-core
computer.

```bash
$ cd cpython
$ ./configure --enable-optimizations --disable-gil --prefix=$HOME/py315-nogil
$ make -j
$ make install
```

### Update execution path

Your Python 3.15 binaries are now in `~/py315-nogil/bin`.  Add the directory to
your path and check the installation:

```bash
$ export PATH=$HOME/py315-nogil/bin:$PATH
$ python3 --version
$ python3 -m pip --version
```

That’s all!  Your custom Python installation is now ready to use!

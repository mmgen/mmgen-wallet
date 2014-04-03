MMGen = Multi-Mode GENerator
============================
##### a Bitcoin cold storage solution for the command line

Install on Microsoft Windows
----------------------------

Installing MMGen on Windows can be divided into four steps:

  1. [Install MinGW and MSYS][01], if you haven't already;
  2. [Install MMGen's dependencies (excluding the bitcoin daemons) and
     MMGen itself][02];
  3. [Install the offline bitcoin daemon (bitcoind)][07]; and
  4. [Build the online "watch-only" bitcoin daemon][03].

Steps 1 and 2 are somewhat lengthy but straightforward.  You may proceed
directly to them by following the links above and then returning to this page.

If you've finished step 2, then you may pause the installation process if you
wish and begin exploring some of MMGen's features as described in [**Getting
Started with MMGen**][08].  To be able to track addresses and create
transactions, however, you must install the bitcoin daemons on your online and
offline machines as described in steps 3 and 4.

The bitcoind on the **offline machine** is used solely to sign transactions and
runs without a blockchain.  Therefore, it will run just fine even on a
low-powered computer such as a netbook.  Installing it is easy.  Just follow the
link on item 3 above.

The **online machine** uses a custom "watch-only" bitcoin daemon to import and
track addresses and maintain the complete blockchain.  These are CPU-intensive
tasks which require a more powerful computer.  You'll also need plenty of free
disk space for the rapidly growing blockchain (~20GB at the time of writing).

The watch-only bitcoind is still new and hasn't yet been included in the stock
Bitcoin distribution.  Therefore, it must be compiled from source code.  On
Windows, this process involves some additional work: compiling and installing
libraries on which bitcoind depends and making some simple edits to source code
and configuration files.

Detailed, step-by-step instructions for installing and building each component
and dependency have been provided to make this process go as smoothly as
possible.  The instructions have been thoroughly tested on the author's build
machine running 32-bit Windows XP.  The target computer is not required to have
an Internet connection.

Be advised that compiling bitcoind on Windows requires some time and patience.
If you're ready to proceed, first read [**A word on text editors**][09] and
install a Unix-capable text editor if you haven't yet done so; then follow the
link on item 4 above to begin the build process.

[01]: MMGenInstallMinGW_MSYS.md
[02]: MMGenInstallDependenciesMSWin.md
[03]: MMGenBuildBitcoindMSWin.md
[07]: MMGenInstallOfflineBitcoind.md
[08]: MMGenGettingStarted.md
[09]: MMGenTextEditors.md

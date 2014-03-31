MMGen = Multi-Mode GENerator
============================
##### a Bitcoin cold storage solution for the command line

Install on Microsoft Windows
----------------------------

The installation process on Windows can be divided into three steps:

  1. [Install MinGW and MSYS][01], if you haven't already;
  2. [Build MMGen's dependencies (excluding the watch-only bitcoind) and
     install MMGen itself][02]; and
  3. [Build the watch-only bitcoind][03].

After the second step you'll be able to use many of MMGen's features.  You
must complete step 3 to be able to track addresses and create transactions,
however.

Getting MMGen up and running on MS Windows requires more work than with Linux,
but your patience will be rewarded with success in the end.  Detailed,
step-by-step instructions for installing and building each component and
dependency have been provided to make the process go as smoothly as possible.

The instructions are designed for a computer not connected to the Internet.
They've been tested on the author's build machine running 32-bit Windows XP.

#### A word on text editors:

The installation process involves some editing of source code and configuration
files.  Windows Notepad is a bad choice for this, because it doesn't handle
the line endings in Unix text files properly.  Therefore, it's recommended you
install a file format-aware text editor like one of the following:

For an easy-to-use editor, try [nano][], available [here][04] as a
precompiled Windows binary.  Just extract `nano.exe` from the archive and copy
it to your path.

For advanced users with some knowledge of vi commands, [Vim][], a full-featured
editor with advanced text highlighting capabilities, will be a better choice.
Grab the Windows installer [here][05] and run it, accepting the defaults.

After installing Vim, you should add its executable directory `C:\Program
Files\Vim\vim74` (the version number may change) to your user path.
Editing paths is explained [here][06].

[01]: MMGenInstallMinGW_MSYS.md
[02]: MMGenInstallDependenciesMSWin.md
[03]: MMGenBuildBitcoindMSWin.md
[06]: MMGenEditPathMSWin.md

[04]: http://mingw-and-ndk.googlecode.com/files/win-mingw-nano.7z
[05]: http://www.vim.org/download.php
[nano]: http://www.nano-editor.org/
[vim]:  http://www.vim.org/

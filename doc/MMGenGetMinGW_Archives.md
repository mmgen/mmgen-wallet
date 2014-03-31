MMGen = Multi-Mode GENerator
============================
##### a Bitcoin cold storage solution for the command line

### Required MinGW Archives:

  * [bsdtar][]
  * [gcc-core-bin][]
  * [gcc-core-dev][]
  * [gcc-core-dll][]
  * [gcc-c++-bin][]
  * [gcc-c++-dev][]
  * [gcc-c++-dll][]
  * [binutils-bin][]
  * [binutils-dev][]
  * [gettext-dev][]
  * [gettext-dll][]
  * [libintl-dll][]
  * [gmp-dev][]
  * [gmp-dll][]
  * [libiconv-dev][]
  * [libiconv-dll][]
  * [mingwrt-dev][]
  * [mingwrt-dll][]
  * [mpc-dev][]
  * [mpc-dll][]
  * [mpfr-dev][]
  * [mpfr-dll][]
  * [pthreads-w32-dev][]
  * [pthreads-w32-dll][]
  * [w32api-dev][]
  * [zlib-dev][]
  * [zlib-dll][]
  * [gettext-bin][]
  * [autoconf2.5-bin][]
  * [automake1.11-bin][]

[bsdtar]: http://sourceforge.net/projects/mingw/files/MinGW/Extension/bsdtar/basic-bsdtar-2.8.3-1/basic-bsdtar-2.8.3-1-mingw32-bin.zip
[gcc-core-bin]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gcc/Version4/gcc-4.8.1-4/gcc-core-4.8.1-4-mingw32-bin.tar.lzma
[gcc-core-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gcc/Version4/gcc-4.8.1-4/gcc-core-4.8.1-4-mingw32-dev.tar.lzma
[gcc-core-dll]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gcc/Version4/gcc-4.8.1-4/gcc-core-4.8.1-4-mingw32-dll.tar.lzma
[gcc-c++-bin]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gcc/Version4/gcc-4.8.1-4/gcc-c++-4.8.1-4-mingw32-bin.tar.lzma
[gcc-c++-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gcc/Version4/gcc-4.8.1-4/gcc-c++-4.8.1-4-mingw32-dev.tar.lzma
[gcc-c++-dll]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gcc/Version4/gcc-4.8.1-4/gcc-c++-4.8.1-4-mingw32-dll.tar.lzma
[binutils-bin]: http://sourceforge.net/projects/mingw/files/MinGW/Base/binutils/binutils-2.24/binutils-2.24-1-mingw32-bin.tar.xz
[binutils-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/binutils/binutils-2.24/binutils-2.24-1-mingw32-dev.tar.xz
[gettext-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gettext/gettext-0.18.3.1-1/gettext-0.18.3.1-1-mingw32-dev.tar.lzma
[gettext-dll]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gettext/gettext-0.18.3.1-1/gettext-0.18.3.1-1-mingw32-dll.tar.lzma
[libintl-dll]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gettext/gettext-0.18.1.1-2/libintl-0.18.1.1-2-mingw32-dll-8.tar.lzma
[gmp-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gmp/gmp-5.1.2/gmp-5.1.2-1-mingw32-dev.tar.lzma
[gmp-dll]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gmp/gmp-5.1.2/gmp-5.1.2-1-mingw32-dll.tar.lzma
[libiconv-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/libiconv/libiconv-1.14-3/libiconv-1.14-3-mingw32-dev.tar.lzma
[libiconv-dll]: http://sourceforge.net/projects/mingw/files/MinGW/Base/libiconv/libiconv-1.14-3/libiconv-1.14-3-mingw32-dll.tar.lzma
[mingwrt-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/mingw-rt/mingwrt-4.0.3/mingwrt-4.0.3-1-mingw32-dev.tar.lzma
[mingwrt-dll]: http://sourceforge.net/projects/mingw/files/MinGW/Base/mingw-rt/mingwrt-4.0.3/mingwrt-4.0.3-1-mingw32-dll.tar.lzma
[mpc-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/mpc/mpc-1.0.1-2/mpc-1.0.1-2-mingw32-dev.tar.lzma
[mpc-dll]: http://sourceforge.net/projects/mingw/files/MinGW/Base/mpc/mpc-1.0.1-2/mpc-1.0.1-2-mingw32-dll.tar.lzma
[mpfr-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/mpfr/mpfr-3.1.2-2/mpfr-3.1.2-2-mingw32-dev.tar.lzma
[mpfr-dll]: http://sourceforge.net/projects/mingw/files/MinGW/Base/mpfr/mpfr-3.1.2-2/mpfr-3.1.2-2-mingw32-dll.tar.lzma
[pthreads-w32-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/pthreads-w32/pthreads-w32-2.9.1/pthreads-w32-2.9.1-1-mingw32-dev.tar.lzma
[pthreads-w32-dll]: http://sourceforge.net/projects/mingw/files/MinGW/Base/pthreads-w32/pthreads-w32-2.9.1/pthreads-w32-2.9.1-1-mingw32-dll.tar.lzma
[w32api-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/w32api/w32api-4.0.3/w32api-4.0.3-1-mingw32-dev.tar.lzma
[zlib-dev]: http://sourceforge.net/projects/mingw/files/MinGW/Base/zlib/zlib-1.2.8/zlib-1.2.8-1-mingw32-dev.tar.lzma
[zlib-dll]: http://sourceforge.net/projects/mingw/files/MinGW/Base/zlib/zlib-1.2.8/zlib-1.2.8-1-mingw32-dll.tar.lzma
[gettext-bin]: http://sourceforge.net/projects/mingw/files/MinGW/Base/gettext/gettext-0.18.3.1-1/gettext-0.18.3.1-1-mingw32-bin.tar.lzma
[autoconf2.5-bin]: http://sourceforge.net/projects/mingw/files/MinGW/Extension/autoconf/autoconf2.5/autoconf2.5-2.68-1/autoconf2.5-2.68-1-mingw32-bin.tar.lzma
[automake1.11-bin]: http://sourceforge.net/projects/mingw/files/MinGW/Extension/automake/automake1.11/automake1.11-1.11.1-1/automake1.11-1.11.1-1-mingw32-bin.tar.lzma

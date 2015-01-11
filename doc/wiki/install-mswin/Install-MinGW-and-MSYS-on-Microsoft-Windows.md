MinGW (Minimal GNU for Windows) provides the gcc compiler and related tools for
compiling source code into Windows binaries.  MSYS provides a Unix-like
environment with basic Unix shell commands.  MinGW and MSYS are part of the
same project and are designed to be used together.

Complete hypertexed lists of the required MinGW and MSYS archive files are
provided below for convenient downloading.  Save the archives into two separate
temporary directories (`mingw` and `msys`, for example).

> * [MinGW archive list][02]
> * [MSYS archive list][03]

##### Note: these lists were up to date at the time of writing (April 2014).  More recent versions may be available in the [MinGW repository][01] as you read this, but hunting for them isn't likely to be worth your time.


Unpack the basic-bsdtar archive (in the MinGW archives) and copy the executable
`basic-bsdtar.exe` to your path (e.g. `C:\WINDOWS\system32`).

From the DOS prompt, run `mkdir C:\mingw` to create the directory `C:\mingw`.
Run `cd C:\mingw` to move to the directory.  Unpack each of the MinGW archives
(except for `basic-bsdtar`) as follows:

		basic-bsdtar -xf <path to archive>

Create a `C:\msys` directory the same way, move to it and repeat the above
unpacking procedure with the MSYS archives.

Add `C:\mingw\bin` to your user path.  Consult [this page][05] for instructions
on editing your user path.

Close the command prompt window and open a new one. Launch the MSYS shell with
the command `C:\msys\bin\bash.exe --login`.  You'll now be in the home
directory of your MSYS environment.

If you want be able to launch MSYS from an icon instead of typing the above
command all the time, then do the following: Make a copy of the "Command Line"
icon on your desktop and rename it to "MSYS".  Right click on the icon, select
"Properties" and change the highlighted command path to `C:\msys\bin\bash.exe
--login`.  You may also want to change the "Home Folder" field to your MSYS home
directory, `C:\msys\home\Admin` for the Admin user.

Note: At this point you're advised to read [**A word on text editors**][00]
before proceeding further with your installation.

Run the command `mount c:/mingw /mingw` to include your MinGW installation in
the MSYS tree.  So you won't have to run this command every time you log in to
MSYS, open the file `/etc/fstab` in your text editor and add the line `c:/mingw
/mingw` (if it's not already there).

#### Unix commands and environment:

If you're new to Unix, you should learn a few key commands:

> * `ls` - view directory contents (`ls -l` for a long view)
> * `rm` - remove files (`rm -r` to remove entire directory trees)
> * `rmdir` - remove an empty directory
> * `cp` - copy a file (`cp -a` to copy directory trees)
> * `mv` - move a file or directory
> * `cat` - output a file to screen
> * `less` - view a file page-by-page, with scrollback

Command help texts can be accessed with the `--help` switch.  The MSYS root
directory is `/`.  Drive letter `C:` can be accessed as `/c/`.

Environmental variables may be viewed with the `env` command.  Individual
variables may be displayed like this:

		$ echo $PATH

and set like this:

		$ set PATH=$PATH:/home/Admin/bin

Sometimes variables must be exported to be visible to called programs:

		$ export PATH

[00]: A-word-on-text-editors
[01]: http://sourceforge.net/projects/mingw/files/
[02]: Required-MinGW-Archives
[03]: Required-MSYS-Archives
[05]: Editing-the-user-path-in-Windows

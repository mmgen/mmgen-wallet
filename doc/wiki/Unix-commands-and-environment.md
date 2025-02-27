### Unix commands: a very brief summary

| Command | Action                                                  |
|:--------|:--------------------------------------------------------|
| `ls`    | view directory contents (`ls -l` for a long view)       |
| `rm`    | remove files (`rm -r` to remove entire directory trees) |
| `rmdir` | remove an empty directory                               |
| `cp`    | copy a file (`cp -a` to copy directory trees)           |
| `mv`    | move a file or directory                                |
| `cat`   | output a file to screen                                 |
| `less`  | view a file page-by-page, with scrollback               |

Command help texts can be accessed with the `--help` switch.  Directories are
separated by `/`, not `\`.  The root of the filesystem is `/`.  Drive letter
`C:` is expressed as `/c/`.

### Environment variables in Unix

Environmental variables may be viewed with the `env` command.  Individual
variables may be viewed like this:

```text
$ echo $PATH
```

and set like this:

```text
$ PATH=$PATH:/home/<username>/bin
```

Sometimes variables must be exported to be visible to called programs:

```text
$ export PATH
```

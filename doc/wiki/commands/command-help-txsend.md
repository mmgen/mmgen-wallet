```text
  MMGEN-TXSEND: Send a signed MMGen cryptocoin transaction
  USAGE:        mmgen-txsend [opts] [signed transaction file]
  OPTIONS:
  -h, --help      Print this help message
      --longhelp  Print help message for long (global) options
  -a, --autosign  Send an autosigned transaction created by ‘mmgen-txcreate
                  --autosign’.  The removable device is mounted and unmounted
                  automatically. The transaction file argument must be omitted
                  when using this option
  -A, --abort     Abort an unsent transaction created by ‘mmgen-txcreate
                  --autosign’ and delete it from the removable device.  The
                  transaction may be signed or unsigned.
  -d, --outdir  d Specify an alternate directory 'd' for output
  -q, --quiet     Suppress warnings; overwrite files without prompting
  -s, --status    Get status of a sent transaction (or the current transaction,
                  whether sent or unsent, when used with --autosign)
  -v, --verbose   Be more verbose
  -y, --yes       Answer 'yes' to prompts, suppress non-essential output

  MMGEN v15.1.dev18              March 2025                    MMGEN-TXSEND(1)
```

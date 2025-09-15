```text
  MMGEN-TXSEND: Send a signed MMGen cryptocoin transaction
  USAGE:        mmgen-txsend [opts] [signed transaction file]
  OPTIONS:
  -h, --help       Print this help message
      --longhelp   Print help message for long (global) options
  -a, --autosign   Send an autosigned transaction created by ‘mmgen-txcreate
                   --autosign’.  The removable device is mounted and unmounted
                   automatically. The transaction file argument must be omitted
                   when using this option
  -A, --abort      Abort an unsent transaction created by ‘mmgen-txcreate
                   --autosign’ and delete it from the removable device.  The
                   transaction may be signed or unsigned.
  -d, --outdir d   Specify an alternate directory 'd' for output
  -H, --dump-hex F Instead of sending to the network, dump the transaction hex
                   to file ‘F’.  Use filename ‘-’ to dump to standard output.
  -m, --mark-sent  Mark the transaction as sent by adding it to the removable
                   device.  Used in combination with --autosign when a trans-
                   action has been successfully sent out-of-band.
  -n, --tx-proxy P Send transaction via public TX proxy ‘P’ (supported proxies:
                   ‘etherscan’).  This is done via a publicly accessible web
                   page, so no API key or registration is required.
  -q, --quiet      Suppress warnings; overwrite files without prompting
  -r, --receipt    Print the receipt of the sent transaction (Ethereum only)
  -s, --status     Get status of a sent transaction (or current transaction,
                   whether sent or unsent, when used with --autosign)
  -t, --test       Test whether the transaction can be sent without sending it
  -T, --txhex-idx N Send only part ‘N’ of a multi-part transaction.  Indexing
                   begins with one.
  -v, --verbose    Be more verbose
  -w, --wait       Wait for transaction confirmation (Ethereum only)
  -x, --proxy P    Connect to TX proxy via SOCKS5h proxy ‘P’ (host:port).
                   Use special value ‘env’ to honor *_PROXY environment vars
                   instead.
  -y, --yes        Answer 'yes' to prompts, suppress non-essential output

  MMGEN-WALLET 16.0.0            September 2025                MMGEN-TXSEND(1)
```

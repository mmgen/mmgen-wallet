The tool API provides a convenient interface to selected methods in the
mmgen.tool module.  Type `pydoc3 mmgen.tool.api` for available methods and
call signatures.

## Examples

### Initialize:

```python
from mmgen.tool.api import tool_api
tool = tool_api()
```

### Key/address generation:

```python
# List available coins:
print(' '.join(tool.coins))

# Initialize a coin/network pair:
proto = tool.init_coin('btc','mainnet')

# Print the available address types for current coin/network, along with a
# description.  If tool.addrtype is unset, the first-listed will be used:
tool.print_addrtypes()

# Set the address type to P2PKH with compressed public key:
tool.addrtype = 'compressed'

# Skip user entropy gathering (not recommended)
tool.usr_randchars = 0

# Generate a random hex secret:
hexsec = tool.randhex()

# Generate the key and address:
wif = tool.hex2wif(hexsec)
addr = tool.wif2addr(wif)

# Generate an LTC regtest Segwit key and address:
proto = tool.init_coin('ltc','regtest')
tool.addrtype = 'segwit'
wif = tool.hex2wif(hexsec)
addr = tool.wif2addr(wif)

# Generate a random LTC regtest Bech32 key/address pair:
tool.addrtype = 'bech32'
wif,addr = tool.randpair()
```

### Mnemonic seed phrase generation:

```python
# Generate an MMGen native mnemonic seed phrase:
mmgen_seed = tool.hex2mn(hexsec)

# Generate a BIP39 mnemonic seed phrase:
bip39_seed = tool.hex2mn(hexsec,fmt='bip39')
```

### Utility methods:

```python
# Reverse the hex string:
hexsec_rev = tool.hexreverse(hexsec)

# Get the HASH160 of the value:
sec_hash160 = tool.hash160(hexsec)

# Convert the value to base58 format:
sec_b58 = tool.hextob58(hexsec)

# Convert the value to base58 check format:
sec_b58chk = tool.hextob58chk(hexsec)

# Convert the byte specification '4G' to an integer:
four_g = tool.bytespec('4G')

# Convert the byte specification '4GB' to an integer:
four_gb = tool.bytespec('4GB')
```

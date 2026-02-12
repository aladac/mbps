# mbps

Command line interface for testing internet bandwidth using speedtest.net.

Based on [sivel/speedtest-cli](https://github.com/sivel/speedtest-cli), repackaged as a modern Python package with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/) output.

## Installation

```
pip install mbps
```

Or with [uv](https://docs.astral.sh/uv/):

```
uv tool install mbps
```

## Usage

```
mbps
```

### Options

| Flag | Description |
|------|-------------|
| `--no-download` | Skip download test |
| `--no-upload` | Skip upload test |
| `--single` | Single connection (simulates typical file transfer) |
| `--bytes` | Display values in bytes instead of bits |
| `--share` | Generate a speedtest.net share results URL |
| `--simple` | Minimal output |
| `--csv` | CSV output (speeds in bit/s) |
| `--csv-delimiter` | Custom CSV delimiter (default `,`) |
| `--csv-header` | Print CSV headers |
| `--json` | JSON output (speeds in bit/s) |
| `--list` | List available servers sorted by distance |
| `--server ID` | Test against a specific server (repeatable) |
| `--exclude ID` | Exclude a server (repeatable) |
| `--mini URL` | Speedtest Mini server URL |
| `--source IP` | Bind to a specific source IP |
| `--timeout SEC` | HTTP timeout in seconds (default 10) |
| `--secure` | Use HTTPS |
| `--no-pre-allocate` | Disable upload pre-allocation (for low-memory systems) |
| `--version` | Show version and exit |

## License

Apache-2.0

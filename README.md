# CTFDump
![Logo](/assets/logo/250%20px.png)

CTFd Dump Tool - When you want to have an offline copy of a CTF.

> Fork of [realgam3/CTFDump](https://github.com/realgam3/CTFDump)

## Features

- **Platform Support**:
    - **CTFd**
    - **rCTF**
    - **GZctf**
    - **AD** (Attack-Defense)
- **Download Sources**:
    - **Google Drive**
    - **Mediafire**
    - Direct downloads (Standard HTTP/HTTPS)
- **Offline Backup**: Downloads challenges, descriptions, files, and more for offline access.
- **resume Support**: Smart configuration file to track downloaded challenges and updates.
- **Authentication**: Supports credential-based login (Username/Password) and Token-based authentication.
- **No Login Mode**: limited dumping for public CTF data without credentials.

## Installation

### Recommended (pipx)

This is the cleanest way to install the tool globally without affecting your system packages.

```bash
pipx install git+https://github.com/FlaBBB/CTFDump.git
```

### via pip

You can also install it directly using pip:

```bash
pip install git+https://github.com/FlaBBB/CTFDump.git
```

### From Source (Development)
W
1. Clone the repository:
   ```bash
   git clone https://github.com/FlaBBB/CTFDump.git
   cd CTFDump
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The general syntax for `CTFDump` is:

```bash
CTFDump <platform> <url> [options]
```

### Arguments

- `platform`: The CTF platform to target. Choices: `CTFd`, `rCTF`.
- `url`: The URL of the CTF (e.g., `https://demo.ctfd.io/`).

### Options

| Flag | Long Flag | Description | Default |
| :--- | :--- | :--- | :--- |
| `-u` | `--username` | Username for login | `None` |
| `-p` | `--password` | Password for login | `None` |
| `-t` | `--token` | Team token (for rCTF) | `None` |
| `-n` | `--no-login` | Skip login (public data only) | `False` |
| `-S` | `--limitsize` | Limit download size in MB | `100` |
| `-F` | `--force` | Ignore config file and re-download | `False` |
| `-v` | `--version` | Show program version | |
| `-h` | `--help` | Show help message | |

### Examples

#### Basic Usage (CTFd)
Dump a CTFd instance using username and password:
```bash
CTFDump CTFd https://demo.ctfd.io/ -u myuser -p mypassword
```

#### rCTF Usage
Dump an rCTF instance using a team token:
```bash
CTFDump rCTF https://rctf.example.com/ -t my-team-token
```

#### No Login
Dump public information without logging in:
```bash
CTFDump CTFd https://demo.ctfd.io/ --no-login
```

#### Limit Download Size
Restrict file downloads to 50MB max:
```bash
CTFDump CTFd https://demo.ctfd.io/ -u user -p pass -S 50
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTE.md) for details on how to get started, report bugs, or submit pull requests.

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

## Kudos

* [mosheDO](https://github.com/mosheDO) - For The rCTF Support
* [hendrykeren](https://github.com/hendrykeren) - For The Awesome Logo

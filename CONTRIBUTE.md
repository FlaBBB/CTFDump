# Contributing to CTFDump

First off, thanks for taking the time to contribute!

The following is a set of guidelines for contributing to CTFDump. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for CTFDump. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

- **Check properly**: Make sure the bug is not caused by your configuration or passing wrong arguments.
- **Search existing issues**: Ensure the bug hasn't already been reported.
- **Open a new Issue**: Explain the behavior you would expect and the actual behavior. Provide a clear and descriptive title.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for CTFDump, including completely new features and minor improvements to existing functionality.

- **Open a new Issue**: Describe the feature you would like to see, why you need it, and how it should work.

### Pull Requests

1. **Fork the repo** and clone it locally.
2. **Create a branch** for your edits (`git checkout -b feature/amazing-feature`).
3. **Make your changes**.
4. **Test your changes** to ensure they work as expected.
5. **Commit your changes** (`git commit -m 'Add some amazing feature'`).
6. **Push to the branch** (`git push origin feature/amazing-feature`).
7. **Open a Pull Request**.

## Developer Guide

### EXTENDING: Adding Support for a New CTF Platform

To support a new CTF platform (e.g., a custom CTFd clone or a different architecture), follow these steps:

1.  **Create a new file** in the `ctfs/` directory (e.g., `ctfs/newplatform.py`).
2.  **Inherit from the `CTF` base class** located in `ctfs/ctf.py`.
3.  **Implement the required methods**:
    *   `apply_argparser(argument_parser)`: Add any platform-specific command-line arguments.
    *   `iter_challenges(self)`: A generator that yields `Challenge` objects. You need to verify the platform version/validity here.
    *   `login(self, no_login=False, **kwargs)`: Handle authentication.
    *   `credential_to_dict(self)`: Return a dictionary of credentials to save in `challenges.json`.
    *   `credential_from_dict(self, credential)`: Load credentials from the dictionary.
4.  **Register the new class**:
    *   Open `ctfs/__init__.py`.
    *   Import your new class.
    *   Add it to the `CTFs` dictionary.

**Example Skeleton:**

```python
from ctfs.ctf import CTF
from core.challange import Challenge

class NewPlatform(CTF):
    def __init__(self, url, max_size=100, force=False):
        super().__init__(url, max_size, force)
        # Initialize platform-specific state

    @staticmethod
    def apply_argparser(argument_parser):
        argument_parser.add_argument("--my-arg", help="Example argument")

    def login(self, no_login=False, **kwargs):
        # Implement login logic
        pass

    def iter_challenges(self):
        # Fetch challenges and yield Challenge objects
        # yield Challenge(ctf=self, ...)
        pass
```

### EXTENDING: Adding a New Download Source

If you want to support a new file hosting service (like Google Drive, Mega, etc.) for downloading challenge files:

1.  **Create a new file** in the `downloader/` directory (e.g., `downloader/mysource.py`).
2.  **Inherit from `BaseSource`** located in `downloader/base.py`.
3.  **Implement the required methods**:
    *   `is_valid(self, url)`: Return `True` if the URL belongs to this source.
    *   `download(self, url, path)`: Handle the download logic. You can use `self.manager.direct_download` or other utilities.
4.  **Register the new source**:
    *   Open `downloader/__init__.py`.
    *   Import your new class.
    *   Add it to the `SOURCES` list.

**Example Skeleton:**

```python
from downloader.base import BaseSource

class MySource(BaseSource):
    def is_valid(self, url: str) -> bool:
        return "myservice.com" in url

    def download(self, url: str, path: str) -> None:
        # Extract direct link or handle download
        pass
```

## Setting Up Development Environment

1. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/CTFDump.git
   cd CTFDump
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the tool locally:
   ```bash
   python CTFDump.py --help
   ```

## Code Style

- Please keep the code consistent with the existing style (Python PEP 8).
- Use descriptive variable names.
- Comment your code where necessary.

Thank you for your contributions!

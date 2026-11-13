# Installation

## Requirements

- Python 3.10 or newer (the package metadata declares support through Python 3.14).
- HTTP API calls use the Python standard library.
- WebSocket calls require the optional `websocket-client` extra.

The SDK is not yet published on PyPI. Install the repository source:

```sh
git clone https://github.com/FingerTrader/fingertrader-python-sdk.git
cd fingertrader-python-sdk
python -m venv .venv
```

Activate the environment, then install:

```sh
# macOS / Linux
. .venv/bin/activate
python -m pip install .

# Windows PowerShell (run instead of the activation line above)
.venv\Scripts\Activate.ps1
python -m pip install .
```

Install WebSocket support when needed:

```sh
python -m pip install '.[websocket]'
```

Verify the public package import:

```sh
python -c "from finger_trader import FingerTraderClient, ApiResponse; print('Finger Trader SDK import OK')"
```

When developing from a checkout, use `python -m pip install -e '.[dev,websocket]'` to install the project and its declared quality tools. On Windows, quote the extra expression as shown and use PowerShell's activation path. On macOS/Linux, shells may differ in activation syntax; the `python -m pip` commands should run through the selected environment's Python.

## Upgrade or uninstall

To update a clone, use Git to select the desired reviewed tag or branch, then reinstall with `python -m pip install .`. Remove the package with `python -m pip uninstall finger-trader-sdk`.

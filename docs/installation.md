# Installation

## Requirements

- Python 3.10 or newer (the package metadata declares support through Python 3.14).
- HTTP API calls use the Python standard library.
- WebSocket calls require the optional `websocket-client` extra.

The SDK is not yet published on PyPI. Install the repository source:

```sh
git clone https://github.com/FingerTrader/finger-trader-python-sdk.git
cd finger-trader-python-sdk
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

## Hosted strategy installation and compatibility

The current source includes `finger_trader.hosted` and its worker. The same source installation above includes the contract JSON assets; the WebSocket extra is not needed for hosted IPC.

```sh
python -c "from finger_trader.hosted import Strategy, Context, Bar; print('Hosted API import OK')"
```

Import success checks the package only. A usable Context is supplied by a compatible Desktop Host during a callback. Running a strategy file directly or launching the private worker without its Host protocol is not a standalone run command.

Desktop development builds verify an exact SDK commit and source inventory. Use the SDK revision pinned by that Desktop build; a newer `main` checkout is not automatically compatible with an older Desktop bundle. Release packaging, signed Runtime installation, and clean-machine acceptance are separate from a source install. See [Hosted strategies](hosted-strategies.md) and [implementation status](quant/p1-hosted-status.md).

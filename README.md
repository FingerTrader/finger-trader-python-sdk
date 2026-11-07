# finger-trader-python-sdk
Official Python SDK foundation for local strategy development, OHLCV bars, basic indicators, lifecycle management, and strategy intent signals.

# Finger Trader Python SDK

**Build. Backtest. Optimize. Automate.**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
![Status](https://img.shields.io/badge/Status-Under%20Development-orange)
![Python](https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white)

The official open-source Python SDK project for **Finger Trader**, a multi-market trading technology platform.

Finger Trader is building an integrated quantitative trading ecosystem that enables developers, quantitative traders, and financial technology teams to develop, test, optimize, and automate trading strategies.

> [!IMPORTANT]
> **Development Status: V1 foundation**
>
> This repository currently provides a local strategy lifecycle, OHLCV bar model, SMA and crossover helpers, three intent signal types, and a chronological bar runner. It is an early development foundation, not a production trading SDK.

---

## Overview

Finger Trader aims to make algorithmic trading accessible to both professional developers and traders without programming experience.

Our quantitative trading ecosystem is designed around two complementary development approaches:

### Python Strategy Development

Develop custom quantitative trading strategies using Python and the Finger Trader SDK.

Designed capabilities include:

- Event-driven strategy development
- Custom technical indicators
- Market data access
- Order and position management
- Historical backtesting
- Parameter optimization
- Paper and live trading integration

### Visual Strategy Development

Create quantitative strategies directly through the Finger Trader Desktop interface without writing code.

The planned Visual Strategy Builder will allow users to:

- Select technical indicators
- Define entry and exit conditions
- Combine trading rules using logical operators
- Configure risk management parameters
- Automatically generate Python strategy code
- Backtest and optimize generated strategies

Both development approaches are designed to share a common strategy execution framework.

---

## Planned Features

### 1. Strategy Framework

- Python-based strategy API
- Event-driven execution
- Strategy lifecycle management
- Custom parameters
- Multi-instrument strategies
- Extensible strategy architecture

### 2. Market Data

- Historical OHLCV data
- Real-time market data integration
- Multiple markets and timeframes
- Local historical data caching
- Market data API integration

### 3. Technical Indicators

Planned built-in indicators include:

- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
- Relative Strength Index (RSI)
- Moving Average Convergence Divergence (MACD)
- Bollinger Bands
- Crossover and crossunder signals

### 4. Backtesting Engine

- Local historical backtesting
- Simulated order execution
- Transaction cost modeling
- Slippage simulation
- Position and portfolio accounting
- Equity curve analysis
- Drawdown analysis
- Performance statistics

### 5. Parameter Optimization

- Parameter grid search
- Multi-core local optimization
- Strategy parameter comparison
- Interactive 3D optimization surfaces
- Performance ranking
- Strategy robustness analysis

### 6. Trading Execution

- Paper trading integration
- Live trading API integration
- Order submission and cancellation
- Order and execution events
- Position monitoring
- Risk management integration

> All features listed above represent the development roadmap and are subject to implementation, testing, and availability.

---

## Architecture

Finger Trader follows a **local-first quantitative computing architecture**.

Computationally intensive operations, including strategy execution, backtesting, technical analysis, and parameter optimization, are designed to run locally whenever practical.

Core trading infrastructure remains connected to authorized services.

```text
                  Finger Trader Desktop
                           |
                  Visual Strategy Builder
                           |
                  Finger Trader Python SDK
                           |
                    Local Quant Runtime
                           |
           +---------------+---------------+
           |               |               |
      Strategy Engine  Backtesting    Optimization
           |               |               |
           +---------------+---------------+
                           |
                    Data / API Layer
                           |
           +---------------+---------------+
           |                               |
       Market Data                    Trading API
                                           |
                                    OMS / Risk Control
```

### Architecture Principles

**Local First**

Execute computationally intensive strategy workloads locally whenever practical.

**Unified Strategy API**

Provide consistent strategy interfaces across backtesting, paper trading, and live trading.

**Modular Design**

Keep market data, indicators, strategy execution, and order management decoupled.

**Extensibility**

Support custom strategies, indicators, quantitative tools, and third-party integrations.

**Security**

Maintain account permissions, authorization, and authoritative trading risk controls at the appropriate system boundaries.

---

## Getting Started

### Requirements

- Python 3.10 or newer.
- No runtime dependencies. The build backend is setuptools.

### Install for local development

~~~sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
~~~

### Run the local dual-moving-average example

~~~sh
python examples/dual_ma_strategy.py
~~~

The example feeds deterministic local OHLCV bars in timestamp order and prints strategy signals. It does not connect to market data, submit orders, or simulate fills.

### Run the automated tests

~~~sh
python -m unittest discover -s tests -v
~~~

The V1 package is an initial development foundation, not a production trading or execution SDK release.

## Example Strategy

The runnable example is examples/dual_ma_strategy.py. It uses the public SDK API:

~~~python
from finger_trader import StrategyRunner
from examples.dual_ma_strategy import DualMovingAverageStrategy, create_demo_bars

strategy = DualMovingAverageStrategy(short_period=2, long_period=3)
signals = StrategyRunner(strategy).run(create_demo_bars())

for signal in signals:
    print(type(signal).__name__, signal.symbol, signal.timestamp, signal.reason)
~~~

Signals express strategy intent only. This example sends no order and reports no execution or fill.

## Quantitative Trading Workflow

The long-term strategy workflow is intended to be:

**Create → Develop → Backtest → Optimize → Validate → Deploy**

Only local strategy development and chronological signal generation are available in this V1 foundation. Backtesting, optimization, validation tooling, and deployment are roadmap items.

### Step 1 — Create

Create a Python strategy or generate one using the Visual Strategy Builder.

### Step 2 — Develop

Implement trading rules, technical indicators, entry conditions, exit conditions, and risk parameters.

### Step 3 — Backtest (planned)

A local backtesting engine is planned; this repository does not yet simulate orders or performance.

### Step 4 — Optimize (planned)

Parameter sweeps and performance comparison are planned and are not available in this V1 foundation.

### Step 5 — Validate (planned)

Validation and robustness analysis tools are planned.

### Step 6 — Deploy (planned)

Paper and live execution integrations are planned and are not part of this SDK foundation.

---

## Documentation

The current installation and runnable example instructions are in this README. Additional documentation is planned to include:

| Documentation | Description |
|---|---|
| Installation Guide | Python environment and SDK setup |
| Quick Start | Build your first quantitative strategy |
| Strategy API | Strategy classes, events, and lifecycle |
| Market Data API | Historical and real-time market data |
| Technical Indicators | Built-in and custom indicators |
| Order API | Orders, executions, and positions |
| Backtesting | Historical simulation and performance |
| Optimization | Parameter sweeps and analysis |
| Paper Trading | Simulated real-time strategy execution |
| Live Trading | Authorized trading API integration |

Documentation will be published progressively alongside SDK releases.

---

## Developer Ecosystem

Finger Trader aims to build an open ecosystem for quantitative trading developers.

The ecosystem is intended to support:

- Custom quantitative trading strategies
- Third-party trading tools
- Custom technical indicators
- Market data integrations
- Strategy templates
- Developer-created analytics
- Community collaboration
- Strategy and tool distribution

Developers will be able to build independent tools using the SDK and integrate them with supported Finger Trader services.

---

## Roadmap

| Phase | Development Focus | Status |
|---|---|---|
| Phase 1 | Python SDK package, public data and signal foundations | V1 foundation |
| Phase 2 | Strategy lifecycle, SMA, and crossover helpers | V1 foundation |
| Phase 3 | Chronological local bar dispatcher | V1 foundation |
| Phase 4 | Historical backtesting engine | Planned |
| Phase 5 | Parameter optimization | Planned |
| Phase 6 | Visual Strategy Builder integration | Planned |
| Phase 7 | Paper trading integration | Planned |
| Phase 8 | Live trading API integration | Planned |

Roadmap priorities and availability may change during development.

---

## Contributing

We welcome feedback, suggestions, and contributions from the developer community.

As the project evolves, we plan to publish:

- Contribution guidelines
- Development environment setup
- Coding standards
- Testing instructions
- Pull request guidelines

For now, please use GitHub Issues to share technical feedback or suggestions.

---

## License

This project is licensed under the **Apache License 2.0**.

See the [LICENSE](LICENSE) file for details.

The open-source license applies to the software distributed under this repository's license.

It does not automatically grant access to proprietary trading infrastructure, licensed market data, brokerage services, or restricted trading APIs.

---

## Disclaimer

Finger Trader Python SDK is a software development project.

Trading financial instruments involves risk, including the potential loss of capital.

Historical backtesting results and simulated performance do not guarantee future results.

Access to market data, trading APIs, and execution services may be subject to account eligibility, applicable permissions, third-party agreements, and regulatory requirements.

---

## Official Repository

**Finger Trader Python SDK**

https://github.com/FingerTrader/finger-trader-python-sdk

---

**Finger Trader — Build Your Trading Strategy.**


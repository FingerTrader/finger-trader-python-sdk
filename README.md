# finger-trader-python-sdk
Official Python SDK for Finger Trader, providing algorithmic trading, market data access, strategy development, backtesting, parameter optimization, and integration with trading APIs.

# Finger Trader Python SDK

**Build. Backtest. Optimize. Automate.**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
![Status](https://img.shields.io/badge/Status-Under%20Development-orange)
![Python](https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white)

The official open-source Python SDK project for **Finger Trader**, a multi-market trading technology platform.

Finger Trader is building an integrated quantitative trading ecosystem that enables developers, quantitative traders, and financial technology teams to develop, test, optimize, and automate trading strategies.

> [!IMPORTANT]
> **Development Status: Under Active Development**
>
> The Finger Trader Python SDK is currently being developed. Public APIs, installation instructions, and executable examples will be published progressively.
>
> The SDK is not yet available as a production-ready release.

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

The SDK is currently under development.

Installation instructions and the first runnable examples will be published when the initial release becomes available.

Future installation methods may include:

- Installation from PyPI
- Installation from GitHub
- Local development installation

Please watch this repository for release announcements and development updates.

---

## Example Strategy

The following code illustrates the intended SDK development experience.

**This is a conceptual API example, not executable code from a released SDK.**

```python
from finger_trader import Strategy


class DualMovingAverage(Strategy):

    def on_bar(self, bar):
        fast_ma = self.sma(20)
        slow_ma = self.sma(60)

        if self.crosses_above(fast_ma, slow_ma):
            self.buy(quantity=100)

        elif self.crosses_below(fast_ma, slow_ma):
            self.close()
```

The final API may differ as the SDK implementation evolves.

---

## Quantitative Trading Workflow

The intended strategy development workflow is:

**Create → Develop → Backtest → Optimize → Validate → Deploy**

### Step 1 — Create

Create a Python strategy or generate one using the Visual Strategy Builder.

### Step 2 — Develop

Implement trading rules, technical indicators, entry conditions, exit conditions, and risk parameters.

### Step 3 — Backtest

Evaluate the strategy against historical market data using the local backtesting engine.

### Step 4 — Optimize

Test different parameter combinations and compare results using performance metrics and interactive optimization charts.

### Step 5 — Validate

Review trading costs, drawdowns, out-of-sample performance, and strategy robustness.

### Step 6 — Deploy

Run validated strategies in supported paper trading environments or connect to authorized live trading services.

---

## Documentation

Official SDK documentation is planned to include:

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
| Phase 1 | Python SDK core architecture | Planned |
| Phase 2 | Strategy API and technical indicators | Planned |
| Phase 3 | Local strategy runtime | Planned |
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


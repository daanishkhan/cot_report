# Quick Start Guide

## Setup (First Time Only)

1. **Create virtual environment and install dependencies:**
   ```bash
   make setup-env
   source .venv/bin/activate
   uv pip install -e .
   ```

## Fetch COT Data

2. **Download all historical COT data:**
   ```bash
   make fetch-data
   ```

   This will:
   - Fetch data from 1986 to present
   - Download all 7 report types
   - Save to `data/` directory as parquet files
   - Takes 5-10 minutes depending on connection

## Plot Trader Positions

3. **Interactive plotting:**
   ```bash
   make plot
   ```

   This will show available contracts and let you choose which to plot.

## Example Code

```python
from main import COTDataManager, COTPlotter

# Load existing data
manager = COTDataManager()
manager.load_from_parquet()

# See available contracts
contracts = manager.get_available_contracts('legacy_fut')
print(f"Available contracts: {len(contracts)}")
print(contracts[:10])  # First 10

# Plot a specific contract
plotter = COTPlotter()
plotter.plot_trader_positions(
    manager.dataframes['legacy_fut'],
    contract_name='GOLD - COMMODITY EXCHANGE INC.',
    report_type='legacy_fut'
)
```

## Understanding the Charts

The bar charts show **net positions** (Long - Short) for three trader groups:

- **Blue Bars**: Large Speculators (hedge funds, large traders)
- **Red Bars**: Large Commercials (producers, merchants, hedgers)
- **Yellow Bars**: Small Speculators (retail traders)

**Positive values** = Net Long (more long than short positions)
**Negative values** = Net Short (more short than long positions)

## Common Contracts

Some popular contracts you might want to analyze:
- `GOLD - COMMODITY EXCHANGE INC.`
- `SILVER - COMMODITY EXCHANGE INC.`
- `CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE`
- `E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE`
- `BITCOIN - CHICAGO MERCANTILE EXCHANGE`
- `EURO FX - CHICAGO MERCANTILE EXCHANGE`

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make setup-env` | Create virtual environment and install uv |
| `make install` | Install all dependencies |
| `make fetch-data` | Download all COT data |
| `make plot` | Interactive plotting tool |
| `make list-contracts` | List all available contracts |
| `make validate CONTRACT=<name> DATE=<date>` | Validate raw COT data for a contract |
| `make clean` | Delete all downloaded data |

### Validate Examples

Check raw COT data values:
```bash
make validate CONTRACT=CAD DATE=2024-10-08
make validate CONTRACT=GOLD DATE=2024-10-15
```

## Search Shortcuts

The plotter supports common currency and commodity codes:

- **CAD** → Canadian Dollar
- **EUR** → Euro FX
- **GBP** → British Pound
- **JPY** → Japanese Yen
- **CRUDE** → Crude Oil
- **GOLD** → Gold
- **ES** → E-Mini S&P 500
- **BITCOIN** → Bitcoin

Just type these codes when searching!

## Troubleshooting

**Problem**: "No data found for contract"
**Solution**: Run `make fetch-data` first to download data

**Problem**: Module not found errors
**Solution**: Make sure venv is activated: `source .venv/bin/activate`

**Problem**: Plot not showing
**Solution**: If running headless, save to file instead:
```python
import matplotlib
matplotlib.use('Agg')  # Add this before importing pyplot
```

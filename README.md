# COT Reports Analysis

A Python tool for fetching, analyzing, and visualizing Commitment of Traders (COT) reports from the CFTC.

## Features

- **Comprehensive Data Fetching**: Downloads all available COT data going back to 1986
- **Multiple Report Types**: Supports all 7 COT report types (Legacy, Disaggregated, TFF, etc.)
- **Automatic Consolidation**: Handles format changes and merges data across different report periods
- **Parquet Storage**: Efficient data storage organized by report type and contract
- **Visualization**: Bar chart plotting of trader positions (Large Speculators, Large Commercials, Small Speculators)

## Setup

### 1. Environment Setup

```bash
make setup-env
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
uv pip install -e .
```

Or using pip:

```bash
pip install -e .
```

## Usage

### Fetch All COT Data

This will download all available historical COT data and save it to parquet files:

```bash
cd src
python main.py
```

This process may take several minutes as it fetches:
- Legacy Futures-only reports
- Legacy Futures-and-Options Combined reports
- Supplemental Futures-and-Options reports
- Disaggregated Futures-only reports
- Disaggregated Futures-and-Options reports
- Traders in Financial Futures (TFF) reports
- TFF Futures-and-Options Combined reports

Data is saved to:
- `data/by_report_type/` - One parquet file per report type
- `data/by_contract/` - One parquet file per unique contract (consolidated across report types)

### Plot Trader Positions

Use the interactive example script:

```bash
python example_plot.py
```

Or use programmatically:

```python
from main import COTDataManager, COTPlotter

# Initialize and load data
manager = COTDataManager(data_dir="data")
manager.load_from_parquet()

# Get available contracts
contracts = manager.get_available_contracts('legacy_fut')
print(contracts)

# Plot a specific contract
plotter = COTPlotter()
plotter.plot_trader_positions(
    manager.dataframes['legacy_fut'],
    contract_name='GOLD - COMMODITY EXCHANGE INC.',
    report_type='legacy_fut',
    start_date='2020-01-01',  # Optional
    end_date='2023-12-31'      # Optional
)
```

## Data Structure

### Trader Categories (Legacy Reports)

The bar charts display net positions for three trader categories:

- **Large Commercials (Red)**: Commercial hedgers with large positions (e.g., producers, merchants)
- **Large Speculators (Blue)**: Non-commercial traders with large positions (e.g., hedge funds, CTAs)
- **Small Speculators (Yellow)**: Non-reportable traders with smaller positions (retail traders)

### Report Types

| Report Type | Code | Description |
|-------------|------|-------------|
| Legacy Futures-only | `legacy_fut` | Traditional COT report for futures only |
| Legacy Futures-and-Options | `legacy_futopt` | Combined futures and options positions |
| Supplemental | `supplemental_futopt` | Additional breakdowns for 13 agricultural markets |
| Disaggregated Futures-only | `disaggregated_fut` | More detailed trader categories |
| Disaggregated Futures-and-Options | `disaggregated_futopt` | Detailed categories with options |
| TFF Futures-only | `traders_in_financial_futures_fut` | Financial futures specific |
| TFF Futures-and-Options | `traders_in_financial_futures_futopt` | Financial futures with options |

## Project Structure

```
cot_report/
├── src/
│   ├── main.py           # Main data fetching and management
│   └── example_plot.py   # Interactive plotting examples
├── data/                 # Data storage (gitignored)
│   ├── by_report_type/   # Parquet files by report type
│   └── by_contract/      # Parquet files by contract
├── tools/
│   └── scripts/
│       └── create_venv.sh
├── pyproject.toml
├── Makefile
└── README.md
```

## API Reference

### COTDataManager

Main class for managing COT data:

```python
manager = COTDataManager(data_dir="data")

# Fetch all historical data
manager.fetch_all_data()

# Save to parquet
manager.save_to_parquet(by_report_type=True, by_contract=True)

# Load from parquet
manager.load_from_parquet()

# Get available contracts
contracts = manager.get_available_contracts('legacy_fut')
```

### COTPlotter

Visualization class:

```python
plotter = COTPlotter()

plotter.plot_trader_positions(
    df=dataframe,
    contract_name='CONTRACT NAME',
    report_type='legacy_fut',
    start_date='2020-01-01',  # Optional
    end_date='2023-12-31',    # Optional
    figsize=(14, 8)           # Optional
)
```

## Data Sources

Data is fetched from the CFTC using the [cot_reports](https://github.com/NDelventhal/cot_reports) Python package, which provides access to historical COT reports dating back to 1986.

## Requirements

- Python 3.8+
- pandas
- matplotlib
- cot_reports

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

"""
Example script demonstrating how to plot COT data.

Usage:
    python example_plot.py
"""

from main import COTDataManager, COTPlotter


def search_contracts(contracts, search_term):
    """Search for contracts matching a term."""
    # Map common aliases to full names
    aliases = {
        'CAD': 'CANADIAN DOLLAR',
        'EUR': 'EURO FX',
        'GBP': 'BRITISH POUND',
        'JPY': 'JAPANESE YEN',
        'CHF': 'SWISS FRANC',
        'AUD': 'AUSTRALIAN DOLLAR',
        'NZD': 'NEW ZEALAND DOLLAR',
        'MXN': 'MEXICAN PESO',
        'BRL': 'BRAZILIAN REAL',
        'CRUDE': 'CRUDE OIL',
        'OIL': 'CRUDE OIL',
        'WTI': 'CRUDE OIL, LIGHT SWEET',
        'NATGAS': 'NATURAL GAS',
        'GAS': 'NATURAL GAS',
        'CORN': 'CORN',
        'WHEAT': 'WHEAT',
        'SOYBEAN': 'SOYBEAN',
        'SPX': 'S&P 500',
        'SP500': 'S&P 500',
        'ES': 'E-MINI S&P 500',
        'NQ': 'NASDAQ',
        'NASDAQ': 'NASDAQ',
        'BITCOIN': 'BITCOIN',
        'BTC': 'BITCOIN',
        'ETHER': 'ETHER',
        'ETH': 'ETHER',
    }

    search_term = search_term.upper()

    # Check if it's an alias
    if search_term in aliases:
        search_term = aliases[search_term]

    matches = [c for c in contracts if search_term in c.upper()]
    return matches


def plot_example():
    """Load data and create example plots."""

    # Initialize data manager
    manager = COTDataManager(data_dir="data")

    # Load existing data from parquet (if already fetched)
    print("Loading data from parquet files...")
    try:
        manager.load_from_parquet()
        print(f"Loaded {len(manager.dataframes)} report types")
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Run main.py first to fetch and save data")
        return

    # Get available contracts from legacy futures report
    if 'legacy_fut' not in manager.dataframes:
        print("No legacy futures data available")
        return

    contracts = manager.get_available_contracts('legacy_fut')
    print(f"\n{len(contracts)} contracts available")

    # Interactive mode - let user search and choose a contract
    print("\n" + "=" * 70)
    print("INTERACTIVE COT PLOTTER")
    print("=" * 70)
    print("\nSearch for contracts (e.g., 'CAD', 'GOLD', 'EUR', 'CRUDE')")
    print("Type 'q' to quit\n")

    plotter = COTPlotter()

    while True:
        search_input = input("Search contracts: ").strip()

        if search_input.lower() == 'q':
            break

        if not search_input:
            continue

        # Search for matching contracts
        matches = search_contracts(contracts, search_input)

        if not matches:
            print(f"No contracts found matching '{search_input}'")
            print("\nPopular searches:")
            print("  Currencies: CAD, EUR, GBP, JPY, CHF, AUD, MXN, BRL")
            print("  Commodities: GOLD, SILVER, COPPER, CRUDE, NATGAS")
            print("  Agriculture: CORN, WHEAT, SOYBEAN, CATTLE, COTTON")
            print("  Indices: ES, NQ, SPX")
            print("  Crypto: BITCOIN, ETHER")
            continue

        print(f"\nFound {len(matches)} matching contract(s):")
        for i, contract in enumerate(matches, 1):
            print(f"  {i}. {contract}")

        if len(matches) == 1:
            # Auto-plot if only one match
            print(f"\nPlotting: {matches[0]}")
            plotter.plot_trader_positions(
                manager.dataframes['legacy_fut'],
                contract_name=matches[0],
                report_type='legacy_fut'
            )
        else:
            # Let user choose which one to plot
            choice_input = input(f"\nEnter number to plot (1-{len(matches)}), or press Enter to search again: ").strip()

            if choice_input.isdigit():
                choice = int(choice_input)
                if 1 <= choice <= len(matches):
                    print(f"\nPlotting: {matches[choice-1]}")
                    plotter.plot_trader_positions(
                        manager.dataframes['legacy_fut'],
                        contract_name=matches[choice-1],
                        report_type='legacy_fut'
                    )
                else:
                    print("Invalid choice")


if __name__ == "__main__":
    plot_example()

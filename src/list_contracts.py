"""
List all available contracts in the COT data.
"""

from main import COTDataManager


def list_all_contracts():
    """List all available contracts."""

    manager = COTDataManager(data_dir="data")

    print("Loading data from parquet files...")
    try:
        manager.load_from_parquet()
        print(f"Loaded {len(manager.dataframes)} report types\n")
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Run 'make fetch-data' first to download COT data")
        return

    if 'legacy_fut' not in manager.dataframes:
        print("No legacy futures data available")
        return

    contracts = manager.get_available_contracts('legacy_fut')

    print(f"Found {len(contracts)} contracts in legacy_fut report:\n")
    print("=" * 80)

    for i, contract in enumerate(contracts, 1):
        print(f"{i:3d}. {contract}")

    print("\n" + "=" * 80)
    print(f"\nTotal: {len(contracts)} contracts")

    # Search examples
    print("\n\nTo search for specific contracts, look for these keywords:")
    keywords = ['CANADIAN', 'DOLLAR', 'GOLD', 'SILVER', 'EURO', 'CRUDE', 'BITCOIN',
                'YEN', 'POUND', 'FRANC', 'CORN', 'WHEAT', 'SOYBEAN', 'CATTLE', 'TREASURY']

    print("\nSample searches:")
    for keyword in keywords:
        matches = [c for c in contracts if keyword in c.upper()]
        if matches:
            print(f"  '{keyword}': {len(matches)} match(es)")
            for match in matches[:2]:
                print(f"    - {match}")


if __name__ == "__main__":
    list_all_contracts()

"""
Validate COT data by showing raw values for a specific contract and date.
"""

from main import COTDataManager
import pandas as pd


def validate_cot_data(contract_search, date_search=None):
    """
    Show raw COT data for validation.

    Args:
        contract_search: Contract name or search term
        date_search: Optional date to filter (YYYY-MM-DD format)
    """
    manager = COTDataManager(data_dir='data')

    print("Loading data...")
    manager.load_from_parquet()

    df = manager.dataframes['legacy_fut']

    # Find contract column
    contract_col = None
    for col in df.columns:
        if 'market' in col.lower() or 'contract' in col.lower():
            contract_col = col
            break

    # Find date column
    date_col = None
    for col in df.columns:
        if 'date' in col.lower() and 'yyyy' in col.lower():
            date_col = col
            break

    # Map common aliases
    aliases = {
        'CAD': 'CANADIAN DOLLAR',
        'EUR': 'EURO FX',
        'GBP': 'BRITISH POUND',
        'JPY': 'JAPANESE YEN',
        'GOLD': 'GOLD',
        'SILVER': 'SILVER',
        'CRUDE': 'CRUDE OIL',
    }

    search_term = contract_search.upper()
    if search_term in aliases:
        search_term = aliases[search_term]

    # Search for contract
    contracts = df[contract_col].unique()
    matches = [c for c in contracts if search_term in c.upper()]

    if not matches:
        print(f"No contracts found matching '{contract_search}'")
        return

    print(f"\nFound {len(matches)} matching contract(s):")
    for i, c in enumerate(matches, 1):
        print(f"  {i}. {c}")

    contract = matches[0]
    print(f"\nUsing: {contract}")

    # Filter data
    data = df[df[contract_col] == contract].copy()
    data[date_col] = pd.to_datetime(data[date_col])
    data = data.sort_values(date_col, ascending=False)

    if date_search:
        # Filter by date
        date_search = pd.to_datetime(date_search)
        # Find closest date
        data['date_diff'] = abs(data[date_col] - date_search)
        closest_idx = data['date_diff'].idxmin()
        data = data.loc[[closest_idx]]

    # Find position columns - prefer "Positions" over "Traders"
    comm_long = None
    comm_short = None
    noncomm_long = None
    noncomm_short = None
    small_long = None
    small_short = None

    # First pass: look for "Positions" columns (preferred)
    for col in data.columns:
        col_lower = col.lower()
        if 'positions' in col_lower:
            if 'commercial' in col_lower and 'noncommercial' not in col_lower:
                if 'long' in col_lower and '(all)' in col_lower:
                    comm_long = col
                elif 'short' in col_lower and '(all)' in col_lower:
                    comm_short = col
            elif 'noncommercial' in col_lower and 'spreading' not in col_lower:
                if 'long' in col_lower and '(all)' in col_lower:
                    noncomm_long = col
                elif 'short' in col_lower and '(all)' in col_lower:
                    noncomm_short = col
            elif 'nonreportable' in col_lower:
                if 'long' in col_lower and '(all)' in col_lower:
                    small_long = col
                elif 'short' in col_lower and '(all)' in col_lower:
                    small_short = col

    # Second pass: fallback to "Traders" columns if not found
    if not noncomm_long or not noncomm_short:
        for col in data.columns:
            col_lower = col.lower()
            if 'trader' in col_lower:
                if 'commercial' in col_lower and 'noncommercial' not in col_lower:
                    if 'long' in col_lower and '(all)' in col_lower and not comm_long:
                        comm_long = col
                    elif 'short' in col_lower and '(all)' in col_lower and not comm_short:
                        comm_short = col
                elif 'noncommercial' in col_lower and 'spreading' not in col_lower:
                    if 'long' in col_lower and '(all)' in col_lower and not noncomm_long:
                        noncomm_long = col
                    elif 'short' in col_lower and '(all)' in col_lower and not noncomm_short:
                        noncomm_short = col
                elif 'nonreportable' in col_lower:
                    if 'long' in col_lower and '(all)' in col_lower and not small_long:
                        small_long = col
                    elif 'short' in col_lower and '(all)' in col_lower and not small_short:
                        small_short = col

    # Show the data
    print("\n" + "=" * 80)
    print("RAW COT DATA")
    print("=" * 80)

    # Convert position columns to numeric before iteration
    if comm_long:
        data[comm_long] = pd.to_numeric(data[comm_long], errors='coerce')
    if comm_short:
        data[comm_short] = pd.to_numeric(data[comm_short], errors='coerce')
    if noncomm_long:
        data[noncomm_long] = pd.to_numeric(data[noncomm_long], errors='coerce')
    if noncomm_short:
        data[noncomm_short] = pd.to_numeric(data[noncomm_short], errors='coerce')
    if small_long:
        data[small_long] = pd.to_numeric(data[small_long], errors='coerce')
    if small_short:
        data[small_short] = pd.to_numeric(data[small_short], errors='coerce')

    for idx, row in data.head(10).iterrows():
        print(f"\nDate: {row[date_col].strftime('%Y-%m-%d')}")
        print("-" * 80)

        if comm_long and comm_short:
            cl = row[comm_long]
            cs = row[comm_short]
            print(f"\nLARGE COMMERCIALS:")
            print(f"  Long:  {cl:>15,.0f}")
            print(f"  Short: {cs:>15,.0f}")
            print(f"  Net:   {cl - cs:>15,.0f}  (Long - Short)")

        if noncomm_long and noncomm_short:
            nl = row[noncomm_long]
            ns = row[noncomm_short]
            print(f"\nLARGE SPECULATORS (Non-Commercial):")
            print(f"  Long:  {nl:>15,.0f}")
            print(f"  Short: {ns:>15,.0f}")
            print(f"  Net:   {nl - ns:>15,.0f}  (Long - Short)")

        if small_long and small_short:
            sl = row[small_long]
            ss = row[small_short]
            print(f"\nSMALL SPECULATORS (Non-Reportable):")
            print(f"  Long:  {sl:>15,.0f}")
            print(f"  Short: {ss:>15,.0f}")
            print(f"  Net:   {sl - ss:>15,.0f}  (Long - Short)")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validate_data.py <contract> [date]")
        print("Example: python validate_data.py CAD 2024-10-08")
        print("Example: python validate_data.py GOLD")
        sys.exit(1)

    contract = sys.argv[1]
    date = sys.argv[2] if len(sys.argv) > 2 else None

    validate_cot_data(contract, date)

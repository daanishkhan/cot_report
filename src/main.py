"""
COT Reports Data Fetcher and Analyzer

This script fetches Commitment of Traders (COT) data from the CFTC,
consolidates different report formats, saves to parquet files, and
provides plotting capabilities for trader positions.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cot_reports as cot


class COTDataManager:
    """Manages COT data fetching, storage, and analysis."""

    # All supported report types
    REPORT_TYPES = [
        'legacy_fut',
        'legacy_futopt',
        'supplemental_futopt',
        'disaggregated_fut',
        'disaggregated_futopt',
        'traders_in_financial_futures_fut',
        'traders_in_financial_futures_futopt'
    ]

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the COT Data Manager.

        Args:
            data_dir: Directory to store parquet files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.dataframes: Dict[str, pd.DataFrame] = {}

    def fetch_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Fetch all available COT data for all report types.
        Goes back as far as possible (1986 for most reports).

        Returns:
            Dictionary mapping report types to dataframes
        """
        print("Fetching all COT data (this may take several minutes)...")

        for report_type in self.REPORT_TYPES:
            print(f"\nFetching {report_type}...")
            try:
                # Fetch all available historical data
                df = cot.cot_all(cot_report_type=report_type)

                if df is not None and not df.empty:
                    # Convert Report_Date_as_YYYY-MM-DD to datetime if it exists
                    date_cols = [col for col in df.columns if 'date' in col.lower()]
                    for date_col in date_cols:
                        try:
                            df[date_col] = pd.to_datetime(df[date_col])
                        except:
                            pass

                    self.dataframes[report_type] = df
                    print(f"  ✓ Fetched {len(df):,} records from {df[date_cols[0]].min()} to {df[date_cols[0]].max()}")
                else:
                    print(f"  ✗ No data available for {report_type}")

            except Exception as e:
                print(f"  ✗ Error fetching {report_type}: {str(e)}")

        return self.dataframes

    def consolidate_by_contract(self) -> Dict[str, pd.DataFrame]:
        """
        Consolidate data by unique contracts across different report types.
        Handles format changes by merging data from different report types for the same contract.

        Returns:
            Dictionary mapping contract names to consolidated dataframes
        """
        print("\nConsolidating data by contract...")

        consolidated = {}

        for report_type, df in self.dataframes.items():
            if df.empty:
                continue

            # Find contract name column (varies by report type)
            contract_col = None
            for col in df.columns:
                if 'market' in col.lower() or 'contract' in col.lower():
                    contract_col = col
                    break

            if contract_col is None:
                print(f"  ⚠ Could not find contract column in {report_type}")
                continue

            # Group by contract
            unique_contracts = df[contract_col].unique()

            for contract in unique_contracts:
                contract_data = df[df[contract_col] == contract].copy()

                if contract in consolidated:
                    # Merge with existing data for this contract
                    # Try to find common columns for merging
                    date_col = [col for col in contract_data.columns if 'date' in col.lower()][0]

                    # Combine dataframes, preferring newer data on conflicts
                    consolidated[contract] = pd.concat([
                        consolidated[contract],
                        contract_data
                    ]).drop_duplicates(subset=[date_col], keep='last').sort_values(date_col)
                else:
                    consolidated[contract] = contract_data

        print(f"  ✓ Consolidated {len(consolidated)} unique contracts")
        return consolidated

    def save_to_parquet(self, by_report_type: bool = True, by_contract: bool = True):
        """
        Save dataframes to parquet files.

        Args:
            by_report_type: Save separate files for each report type
            by_contract: Save separate files for each contract
        """
        print("\nSaving data to parquet files...")

        if by_report_type:
            report_dir = self.data_dir / "by_report_type"
            report_dir.mkdir(exist_ok=True)

            for report_type, df in self.dataframes.items():
                if not df.empty:
                    # Clean the dataframe to handle mixed types
                    df_clean = df.copy()

                    # Convert object columns with mixed types to strings
                    for col in df_clean.columns:
                        if df_clean[col].dtype == 'object':
                            try:
                                # Try to convert to numeric first
                                df_clean[col] = pd.to_numeric(df_clean[col], errors='ignore')
                            except:
                                pass

                            # If still object type, convert to string
                            if df_clean[col].dtype == 'object':
                                df_clean[col] = df_clean[col].astype(str)

                    filepath = report_dir / f"{report_type}.parquet"
                    df_clean.to_parquet(filepath, index=False, engine='pyarrow')
                    print(f"  ✓ Saved {report_type} ({len(df_clean):,} records)")

        if by_contract:
            contract_dir = self.data_dir / "by_contract"
            contract_dir.mkdir(exist_ok=True)

            consolidated = self.consolidate_by_contract()
            for contract, df in consolidated.items():
                # Clean the dataframe to handle mixed types
                df_clean = df.copy()

                # Convert object columns with mixed types to strings
                for col in df_clean.columns:
                    if df_clean[col].dtype == 'object':
                        try:
                            # Try to convert to numeric first
                            df_clean[col] = pd.to_numeric(df_clean[col], errors='ignore')
                        except:
                            pass

                        # If still object type, convert to string
                        if df_clean[col].dtype == 'object':
                            df_clean[col] = df_clean[col].astype(str)

                # Clean contract name for filename
                safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in contract)
                safe_name = safe_name.replace(' ', '_')[:100]  # Limit filename length

                filepath = contract_dir / f"{safe_name}.parquet"
                df_clean.to_parquet(filepath, index=False, engine='pyarrow')

            print(f"  ✓ Saved {len(consolidated)} contract files")

    def load_from_parquet(self, report_type: Optional[str] = None) -> pd.DataFrame:
        """
        Load data from parquet files.

        Args:
            report_type: Specific report type to load, or None for all

        Returns:
            DataFrame with loaded data
        """
        if report_type:
            filepath = self.data_dir / "by_report_type" / f"{report_type}.parquet"
            return pd.read_parquet(filepath)
        else:
            # Load all report types
            for report_type in self.REPORT_TYPES:
                filepath = self.data_dir / "by_report_type" / f"{report_type}.parquet"
                if filepath.exists():
                    self.dataframes[report_type] = pd.read_parquet(filepath)
            return self.dataframes

    def get_available_contracts(self, report_type: str) -> List[str]:
        """
        Get list of available contracts for a given report type.

        Args:
            report_type: The COT report type

        Returns:
            List of contract names
        """
        if report_type not in self.dataframes or self.dataframes[report_type].empty:
            return []

        df = self.dataframes[report_type]

        # Find contract column
        for col in df.columns:
            if 'market' in col.lower() or 'contract' in col.lower():
                return sorted(df[col].unique().tolist())

        return []


class COTPlotter:
    """Handles plotting of COT data."""

    @staticmethod
    def plot_trader_positions(
        df: pd.DataFrame,
        contract_name: str,
        report_type: str = 'legacy_fut',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        figsize: Tuple[int, int] = (16, 10)
    ):
        """
        Plot trader positions as time series bar chart with black background.

        Shows net positions (Long - Short) for:
        - Large Speculators (Blue) - Positive = Net Long, Negative = Net Short
        - Large Commercials (Red) - Positive = Net Long, Negative = Net Short
        - Small Speculators (Yellow) - Positive = Net Long, Negative = Net Short

        Defaults to last 5 years of data if no date range specified.

        Args:
            df: DataFrame containing COT data
            contract_name: Name of the contract to plot
            report_type: Type of COT report
            start_date: Optional start date for filtering (defaults to 5 years ago)
            end_date: Optional end date for filtering (defaults to now)
            figsize: Figure size tuple
        """
        # Find date column
        date_col = None
        for col in df.columns:
            if 'date' in col.lower() and 'yyyy' in col.lower():
                date_col = col
                break

        if date_col is None:
            raise ValueError("Could not find date column in dataframe")

        # Filter by contract
        contract_col = None
        for col in df.columns:
            if 'market' in col.lower() or 'contract' in col.lower():
                contract_col = col
                break

        if contract_col is None:
            raise ValueError("Could not find contract column in dataframe")

        plot_df = df[df[contract_col] == contract_name].copy()

        if plot_df.empty:
            print(f"No data found for contract: {contract_name}")
            return

        # Ensure date column is datetime
        plot_df[date_col] = pd.to_datetime(plot_df[date_col])

        # Filter by date range if specified
        # Default to last 5 years if no dates specified
        if not start_date and not end_date:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')

        if start_date:
            plot_df = plot_df[plot_df[date_col] >= pd.to_datetime(start_date)]
        if end_date:
            plot_df = plot_df[plot_df[date_col] <= pd.to_datetime(end_date)]

        # Sort by date
        plot_df = plot_df.sort_values(date_col)

        # For legacy reports, calculate net positions (Long - Short)
        if 'legacy' in report_type.lower():
            # Try different column name formats
            # Format 1: "Commercial Positions-Long (All)"
            # Format 2: "Comm_Positions_Long_All"

            # Find the correct column names - prefer "Positions" over "Traders"
            comm_long = None
            comm_short = None
            noncomm_long = None
            noncomm_short = None
            small_long = None
            small_short = None

            # First pass: look for "Positions" columns (preferred)
            for col in plot_df.columns:
                col_lower = col.lower()
                if 'positions' in col_lower:
                    # Commercial
                    if 'commercial' in col_lower and 'noncommercial' not in col_lower:
                        if 'long' in col_lower and '(all)' in col_lower:
                            comm_long = col
                        elif 'short' in col_lower and '(all)' in col_lower:
                            comm_short = col
                    # Noncommercial (Large Speculators)
                    elif 'noncommercial' in col_lower and 'spreading' not in col_lower:
                        if 'long' in col_lower and '(all)' in col_lower:
                            noncomm_long = col
                        elif 'short' in col_lower and '(all)' in col_lower:
                            noncomm_short = col
                    # Nonreportable (Small Speculators)
                    elif 'nonreportable' in col_lower:
                        if 'long' in col_lower and '(all)' in col_lower:
                            small_long = col
                        elif 'short' in col_lower and '(all)' in col_lower:
                            small_short = col

            # Second pass: fallback to "Traders" columns if not found
            if not noncomm_long or not noncomm_short:
                for col in plot_df.columns:
                    col_lower = col.lower()
                    if 'trader' in col_lower:
                        # Commercial
                        if 'commercial' in col_lower and 'noncommercial' not in col_lower:
                            if 'long' in col_lower and '(all)' in col_lower and not comm_long:
                                comm_long = col
                            elif 'short' in col_lower and '(all)' in col_lower and not comm_short:
                                comm_short = col
                        # Noncommercial (Large Speculators)
                        elif 'noncommercial' in col_lower and 'spreading' not in col_lower:
                            if 'long' in col_lower and '(all)' in col_lower and not noncomm_long:
                                noncomm_long = col
                            elif 'short' in col_lower and '(all)' in col_lower and not noncomm_short:
                                noncomm_short = col
                        # Nonreportable (Small Speculators)
                        elif 'nonreportable' in col_lower:
                            if 'long' in col_lower and '(all)' in col_lower and not small_long:
                                small_long = col
                            elif 'short' in col_lower and '(all)' in col_lower and not small_short:
                                small_short = col

            # Calculate net positions (Long - Short)
            # Positive = Net Long, Negative = Net Short
            trader_data = []

            if comm_long and comm_short:
                plot_df[comm_long] = pd.to_numeric(plot_df[comm_long], errors='coerce').fillna(0)
                plot_df[comm_short] = pd.to_numeric(plot_df[comm_short], errors='coerce').fillna(0)
                plot_df['Commercial_Net'] = plot_df[comm_long] - plot_df[comm_short]
                trader_data.append(('Large Commercials', 'Commercial_Net', 'red'))

            if noncomm_long and noncomm_short:
                plot_df[noncomm_long] = pd.to_numeric(plot_df[noncomm_long], errors='coerce').fillna(0)
                plot_df[noncomm_short] = pd.to_numeric(plot_df[noncomm_short], errors='coerce').fillna(0)
                plot_df['NonCommercial_Net'] = plot_df[noncomm_long] - plot_df[noncomm_short]
                trader_data.append(('Large Speculators', 'NonCommercial_Net', 'blue'))

            if small_long and small_short:
                plot_df[small_long] = pd.to_numeric(plot_df[small_long], errors='coerce').fillna(0)
                plot_df[small_short] = pd.to_numeric(plot_df[small_short], errors='coerce').fillna(0)
                plot_df['NonReportable_Net'] = plot_df[small_long] - plot_df[small_short]
                trader_data.append(('Small Speculators', 'NonReportable_Net', 'yellow'))

            if not trader_data:
                print(f"Could not find position columns for {report_type}")
                print(f"Available columns: {list(plot_df.columns)}")
                return

            # Create the plot with black background
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=figsize, facecolor='black')
            ax.set_facecolor('black')

            # Create time series
            dates = plot_df[date_col].values
            x_pos = range(len(dates))
            n_traders = len(trader_data)

            # Calculate bar width and positions for grouped bars
            total_bar_width = 0.8
            bar_width = total_bar_width / n_traders

            # Create offset positions for each group
            offsets = []
            if n_traders == 3:
                offsets = [-bar_width, 0, bar_width]
            elif n_traders == 2:
                offsets = [-bar_width/2, bar_width/2]
            else:
                offsets = [0]

            # Plot each trader type as bars
            for i, (label, col, color) in enumerate(trader_data):
                values = plot_df[col].values
                positions = [x + offsets[i] for x in x_pos]
                ax.bar(positions, values, width=bar_width, label=label, color=color, alpha=0.8)

            # Formatting
            ax.set_xlabel('Date', fontsize=14, color='white')
            ax.set_ylabel('Net Positions (Long - Short)', fontsize=14, color='white')
            ax.set_title(f'COT Trader Positions - {contract_name} (Last 5 Years)', fontsize=16, fontweight='bold', color='white')

            # Add horizontal line at zero
            ax.axhline(y=0, color='white', linestyle='-', linewidth=0.5, alpha=0.5)

            # Legend with white text
            legend = ax.legend(loc='upper left', fontsize=12, framealpha=0.8)
            legend.get_frame().set_facecolor('black')
            legend.get_frame().set_edgecolor('white')
            for text in legend.get_texts():
                text.set_color('white')

            # Grid
            ax.grid(True, alpha=0.2, color='white', linestyle='--', axis='y')

            # Set x-axis labels (show every nth date to avoid crowding)
            n_ticks = min(15, len(plot_df))
            if n_ticks > 0:
                tick_indices = [int(i * len(plot_df) / n_ticks) for i in range(n_ticks)]
                ax.set_xticks([x_pos[i] for i in tick_indices])
                ax.set_xticklabels([plot_df.iloc[i][date_col].strftime('%Y-%m-%d') for i in tick_indices],
                                  rotation=45, ha='right', color='white')

            # White tick labels
            ax.tick_params(colors='white')

            # Format y-axis with thousands separator
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

            plt.tight_layout()
            plt.show()

            # Reset style
            plt.style.use('default')

        else:
            print(f"Report type {report_type} not yet supported. Use 'legacy_fut'.")


def main():
    """Main execution function."""

    # Initialize data manager
    manager = COTDataManager(data_dir="data")

    # Fetch all data
    print("=" * 70)
    print("COT DATA FETCHER - Fetching all available historical data")
    print("=" * 70)

    manager.fetch_all_data()

    # Save to parquet
    manager.save_to_parquet(by_report_type=True, by_contract=True)

    print("\n" + "=" * 70)
    print("DATA FETCH COMPLETE")
    print("=" * 70)

    # Example: Plot a specific contract
    print("\nExample: Plotting available contracts...")

    # Try to plot from legacy futures (most common)
    if 'legacy_fut' in manager.dataframes and not manager.dataframes['legacy_fut'].empty:
        contracts = manager.get_available_contracts('legacy_fut')
        print(f"\nFound {len(contracts)} contracts in legacy_fut report")
        print(f"First 10 contracts: {contracts[:10]}")

        if contracts:
            print(f"\nTo plot a specific contract, use:")
            print(f"  plotter = COTPlotter()")
            print(f"  plotter.plot_trader_positions(")
            print(f"      manager.dataframes['legacy_fut'],")
            print(f"      contract_name='{contracts[0]}',")
            print(f"      report_type='legacy_fut'")
            print(f"  )")


if __name__ == "__main__":
    main()

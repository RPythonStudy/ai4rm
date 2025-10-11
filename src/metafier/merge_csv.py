import sys
import glob
import pandas as pd

SEPERATOR = '|'

def print_usage():
    print("Usage: python merge_csv.py <base_file_name>")
    print("Example: python merge_csv.py result")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print_usage()

    base = sys.argv[1]
    pattern = f"{base}_*.csv"
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"No files matching '{pattern}' found.")
        sys.exit(1)

    dfs = []
    for i, file in enumerate(files):
        df = pd.read_csv(file, sep=SEPERATOR, encoding='utf-8-sig')
        print(f"\n--- Processing file: {file} ---")
        print(f"Columns for this DataFrame ({len(df.columns)}):")
        # This is the crucial part to check for column name inconsistencies
        for col in df.columns.tolist():
            # Print with delimiters to easily spot leading/trailing spaces
            print(f"  '{col}'") 
        print(df.head(2)) # Show a couple of rows for context
        dfs.append(df)

    merged_df = pd.concat(dfs, ignore_index=True)
    print("\n--- Merged DataFrame Information ---")
    print(f"Merged DataFrame columns ({len(merged_df.columns)}): {merged_df.columns.tolist()}")
    print(merged_df.head())

    merged_df.to_csv(f"{base}-merged.csv", index=False, encoding='utf-8-sig')
    print(f"\nMerged {len(files)} files into '{base}_merged.csv'.")

if __name__ == "__main__":
    main()
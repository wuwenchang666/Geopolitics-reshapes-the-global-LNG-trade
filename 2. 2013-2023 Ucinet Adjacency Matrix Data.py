import pandas as pd
import numpy as np
import os


def convert_edge_to_adjacency(year, input_path):
    """
    Convert edge table data to weighted adjacency matrix for a specific year

    Parameters:
        year: year (for output filename)
        input_path: full path to input CSV file
    """
    try:
        print(f"Processing {year} data...")

        # Read GBK encoded source file
        df = pd.read_csv(input_path, encoding='gbk')
        print(f"Successfully read {year} GBK encoded source file")

        # Extract core columns
        required_cols = ['source', 'target', 'weight']

        # Handle possible column name case issues
        actual_cols = []
        for col in required_cols:
            matching_cols = [c for c in df.columns if c.lower() == col.lower()]
            if matching_cols:
                actual_cols.append(matching_cols[0])
            else:
                raise ValueError(f"Column '{col}' not found in {year} file! Actual columns: {df.columns.tolist()}")

        df_core = df[actual_cols].copy()
        df_core.columns = required_cols  # Standardize to lowercase

        # Ensure weight column is numeric
        df_core['weight'] = pd.to_numeric(df_core['weight'], errors='coerce').fillna(0)

        # Get all unique countries
        all_countries = sorted(list(set(df_core['source'].unique()) | set(df_core['target'].unique())))
        country_count = len(all_countries)
        print(f"Identified {country_count} countries")

        # Create country to index mapping
        country_to_idx = {country: idx for idx, country in enumerate(all_countries)}

        # Create empty weighted adjacency matrix
        adj_matrix = np.zeros((country_count, country_count), dtype=float)

        # Fill matrix
        processed_rows = 0
        for _, row in df_core.iterrows():
            export_country = row['source']
            import_country = row['target']
            weight = row['weight']

            if export_country in country_to_idx and import_country in country_to_idx:
                export_idx = country_to_idx[export_country]
                import_idx = country_to_idx[import_country]
                adj_matrix[export_idx, import_idx] = weight
                processed_rows += 1

        print(f"Processed {processed_rows} trade relationships")

        # Generate output path
        output_dir = os.path.dirname(input_path)
        output_file_name = f"Trade_Weighted_Adjacency_Matrix_{year}.csv"
        output_file_path = os.path.join(output_dir, output_file_name)

        # Save matrix as CSV
        adj_matrix_df = pd.DataFrame(
            adj_matrix,
            index=all_countries,
            columns=all_countries
        )
        adj_matrix_df.to_csv(output_file_path, encoding='utf-8', index=True)
        print(f"Adjacency matrix saved to: {output_file_path}")
        print(f"Matrix dimensions: {country_count} rows × {country_count} columns")

        return {
            'year': year,
            'success': True,
            'output_path': output_file_path,
            'matrix_shape': adj_matrix.shape,
            'num_countries': country_count
        }

    except Exception as e:
        print(f"Failed to process {year}: {str(e)}")
        return {
            'year': year,
            'success': False,
            'error': str(e)
        }


def main():
    """Main function: batch process 2013-2023 data"""

    # Define years and corresponding file paths
    year_files = {}
    for year in range(2013, 2024):
        file_name = f"{year}_Wij_Valid_Trade_Edges.csv"
        # Update this path to your actual file location
        file_path = f"your_file_location/{year}/{file_name}"
        year_files[year] = file_path

    print("=" * 60)
    print("Batch Edge Table to Adjacency Matrix Converter")
    print("=" * 60)
    print(f"Processing years: 2013-2023 (total: {len(year_files)} years)")
    print()

    # Store all processing results
    results = []

    # Process years in order
    for year in sorted(year_files.keys()):
        input_path = year_files[year]

        # Check if file exists
        if not os.path.exists(input_path):
            print(f"Warning: {year} file does not exist, skipping: {input_path}")
            results.append({
                'year': year,
                'success': False,
                'error': 'File not found'
            })
            continue

        # Process data for this year
        result = convert_edge_to_adjacency(year, input_path)
        results.append(result)
        print()

    print("=" * 60)
    print("Processing complete! Summary report:")
    print("=" * 60)

    # Count successes and failures
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]

    print(f"Successfully processed: {len(successful)} years")
    if successful:
        for r in successful:
            print(f"   {r['year']}: {r['num_countries']} countries, matrix {r['matrix_shape']}")

    print(f"Failed to process: {len(failed)} years")
    if failed:
        for r in failed:
            print(f"   {r['year']}: {r.get('error', 'Unknown error')}")

    # Generate summary CSV
    summary_df = pd.DataFrame([
        {
            'Year': r['year'],
            'Status': 'Success' if r.get('success') else 'Failed',
            'Country_Count': r.get('num_countries', 'N/A'),
            'Matrix_Dimensions': f"{r.get('matrix_shape', 'N/A')}",
            'Output_File': r.get('output_path', 'N/A'),
            'Error_Message': r.get('error', '')
        }
        for r in results
    ])

    summary_path = "your_file_location/batch_conversion_summary.csv"
    summary_df.to_csv(summary_path, encoding='utf-8', index=False)
    print()
    print(f"Detailed summary report saved to: {summary_path}")


if __name__ == "__main__":
    main()
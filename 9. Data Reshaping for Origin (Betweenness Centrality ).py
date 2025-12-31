import pandas as pd
import numpy as np
import os

# File paths
input_file = "your_file_location/betweenness_centrality_complete_data.csv"
output_dir = "your_file_location/betweenness_analysis"

# Create output directory
os.makedirs(output_dir, exist_ok=True)

print("=" * 60)
print("Processing file...")
print(f"Input file: {input_file}")
print("=" * 60)

try:
    # Read file - this should be a CSV file based on the previous analysis output
    print("Reading file...")

    # Try different encodings for CSV
    encodings = ['utf-8', 'gbk', 'utf-8-sig', 'gb2312']
    df = None

    for encoding in encodings:
        try:
            df = pd.read_csv(input_file, encoding=encoding)
            print(f"Read successfully using {encoding} encoding!")
            break
        except Exception:
            print(f"{encoding} failed, trying next...")
            continue

    if df is None:
        print("All CSV encoding attempts failed, trying Excel...")
        try:
            df = pd.read_excel(input_file)
            print("Read successfully as Excel!")
        except Exception as e:
            print(f"Excel read also failed: {e}")
            exit()

    print(f"Data shape: {df.shape}")
    print(f"Column names: {list(df.columns)}")
    print("\nFirst 5 rows preview:")
    print(df.head())

    # Clean column names
    df.columns = df.columns.str.strip()

    # Get year column and country columns
    # Assuming first column is year
    year_column = df.columns[0]
    print(f"\nYear column: '{year_column}'")

    # Country columns (all columns except year column)
    countries = [col for col in df.columns if col != year_column]
    print(f"Found {len(countries)} countries")
    print("Country list:")
    for i, country in enumerate(countries):
        print(f"  {i + 1:2d}. {country}")

    # Convert to long format and sort by country-year
    print("\nConverting to long format and sorting...")

    # Use melt to convert
    long_df = pd.melt(
        df,
        id_vars=[year_column],
        value_vars=countries,
        var_name='Country',
        value_name='Betweenness_Centrality_Value'
    )

    # Rename year column
    long_df = long_df.rename(columns={year_column: 'Year'})

    # Sort by country then year
    long_df = long_df.sort_values(['Country', 'Year']).reset_index(drop=True)

    print(f"Conversion complete! Long format data shape: {long_df.shape}")

    print("\nVerifying sorting results:")
    print("China data for first 5 years:")
    china_data = long_df[long_df['Country'] == 'China'].head()
    print(china_data)

    print("\nIndia data for first 5 years:")
    india_data = long_df[long_df['Country'] == 'India'].head()
    print(india_data)

    # Save as Excel file
    output_file_excel = os.path.join(output_dir, "betweenness_by_country.xlsx")

    print(f"\nSaving Excel file: {output_file_excel}")

    with pd.ExcelWriter(output_file_excel, engine='openpyxl') as writer:
        # Save complete data
        long_df.to_excel(writer, sheet_name='All_Data', index=False)

        # Optimize for Origin import
        origin_df = long_df.copy()
        origin_df['Year-Country'] = origin_df['Year'].astype(str) + ' ' + origin_df['Country']
        origin_df = origin_df[['Year-Country', 'Betweenness_Centrality_Value']]
        origin_df.to_excel(writer, sheet_name='Origin_Format', index=False)

        # Calculate yearly Top20 rankings
        print("Calculating yearly Top20 rankings...")

        all_years_rank = []

        for year in sorted(long_df['Year'].unique()):
            year_data = long_df[long_df['Year'] == year]
            # Sort by value descending
            year_rank = year_data.sort_values('Betweenness_Centrality_Value', ascending=False)
            year_rank = year_rank.reset_index(drop=True)
            year_rank['Rank'] = year_rank.index + 1

            # Take top 20
            year_rank_top20 = year_rank.head(20)

            # Add year column for identification
            year_rank_top20.insert(0, 'Year', year)
            all_years_rank.append(year_rank_top20)

        # Combine all years' rankings
        if all_years_rank:
            all_rank_df = pd.concat(all_years_rank, ignore_index=True)
            all_rank_df = all_rank_df[['Year', 'Rank', 'Country', 'Betweenness_Centrality_Value']]
            all_rank_df.to_excel(writer, sheet_name='Yearly_Top20_Rankings', index=False)

    print(f"Excel file saved!")

    # Save as CSV
    output_file_csv = os.path.join(output_dir, "betweenness_by_country.csv")
    long_df.to_csv(output_file_csv, index=False, encoding='utf-8-sig')
    print(f"CSV file saved: {output_file_csv}")

    # Generate statistical report
    print("\nData Statistics Report:")
    print("=" * 60)

    # Basic statistics
    print(f"Data time range: {long_df['Year'].min()} - {long_df['Year'].max()}")
    print(f"Number of countries: {len(countries)}")
    print(f"Number of years: {long_df['Year'].nunique()}")

    # Number of records per country
    print(f"\nNumber of data records per country:")
    country_counts = long_df['Country'].value_counts()
    for country, count in country_counts.head(10).items():
        print(f"  {country}: {count} records")

    if len(country_counts) > 10:
        print(f"  ... and {len(country_counts) - 10} more countries")

    # Yearly champion country
    print(f"\nYearly betweenness centrality champion:")

    champion_by_year = {}
    for year in sorted(long_df['Year'].unique()):
        year_data = long_df[long_df['Year'] == year]
        champion = year_data.loc[year_data['Betweenness_Centrality_Value'].idxmax()]
        champion_by_year[year] = (champion['Country'], champion['Betweenness_Centrality_Value'])
        print(f"  {year}: {champion['Country']} ({champion['Betweenness_Centrality_Value']:.6f})")

    # Most consistent Top5 countries
    print(f"\nChampion frequency statistics:")
    champion_counts = {}
    for year, (country, value) in champion_by_year.items():
        champion_counts[country] = champion_counts.get(country, 0) + 1

    # Sort by champion frequency
    sorted_champions = sorted(champion_counts.items(), key=lambda x: x[1], reverse=True)
    for country, count in sorted_champions[:5]:
        print(f"  {country}: {count} championships ({count / len(champion_by_year) * 100:.1f}%)")

    # Generate worksheet with separate sheet per country
    print(f"\nGenerating worksheet with separate sheets per country...")
    output_file_by_country = os.path.join(output_dir, "betweenness_by_country_separate_sheets.xlsx")

    with pd.ExcelWriter(output_file_by_country, engine='openpyxl') as writer:
        # Group by country, each country gets its own sheet
        for country in countries[:15]:  # Only process first 15 countries to avoid file being too large
            country_data = long_df[long_df['Country'] == country].copy()
            country_data = country_data.sort_values('Year')

            # Sheet name limited to 31 characters, take first 10 characters
            sheet_name = country[:10] if len(country) > 10 else country
            country_data.to_excel(writer, sheet_name=sheet_name, index=False)

        # Add a summary sheet
        summary_df = pd.DataFrame({
            'Statistic': ['Number of Countries', 'Year Range', 'Total Data Points', 'Average', 'Maximum', 'Minimum'],
            'Value': [
                len(countries),
                f"{long_df['Year'].min()}-{long_df['Year'].max()}",
                len(long_df),
                f"{long_df['Betweenness_Centrality_Value'].mean():.6f}",
                f"{long_df['Betweenness_Centrality_Value'].max():.6f}",
                f"{long_df['Betweenness_Centrality_Value'].min():.6f}"
            ]
        })
        summary_df.to_excel(writer, sheet_name='Data_Summary', index=False)

    print(f"Country-specific sheets file saved: {output_file_by_country}")

except FileNotFoundError:
    print(f"File not found: {input_file}")
    print("Please check the file path.")

except Exception as e:
    print(f"Error during processing: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Processing complete!")
print("=" * 60)
print("\nGenerated files:")
print(f"1. betweenness_by_country.xlsx - Main file containing:")
print("   - 'All_Data' sheet: Complete data sorted by country-year")
print("   - 'Origin_Format' sheet: Two-column format for Origin import")
print("   - 'Yearly_Top20_Rankings' sheet: Yearly ranking data")
print(f"2. betweenness_by_country.csv - CSV version")
print(f"3. betweenness_by_country_separate_sheets.xlsx - Separate sheet per country")
print("\nUsage suggestions:")
print("- Use 'Origin_Format' sheet for Origin import")
print("- Or use 'All_Data' sheet and group by 'Country' column in Origin")
import pandas as pd
import os
from collections import Counter

# Define file paths
file_paths = {
    2013: "your_file_location/2013/Structural_Holes_both_2013.csv",
    2014: "your_file_location/2014/Structural_Holes_both_2014.csv",
    2015: "your_file_location/2015/Structural_Holes_both_2015.csv",
    2016: "your_file_location/2016/Structural_Holes_both_2016.csv",
    2017: "your_file_location/2017/Structural_Holes_both_2017.csv",
    2018: "your_file_location/2018/Structural_Holes_both_2018.csv",
    2019: "your_file_location/2019/Structural_Holes_both_2019.csv",
    2020: "your_file_location/2020/Structural_Holes_both_2020.csv",
    2021: "your_file_location/2021/Structural_Holes_both_2021.csv",
    2022: "your_file_location/2022/Structural_Holes_both_2022.csv",
    2023: "your_file_location/2023/Structural_Holes_both_2023.csv"
}

# Initialize storage
effective_frequency = Counter()
constraint_frequency = Counter()
all_years_data = {}

# Read all years data and count frequencies
for year, file_path in file_paths.items():
    try:
        # Multi-encoding reading
        for encoding in ['utf-8', 'gbk', 'ISO-8859-1']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except:
                continue

        # Standardize column names
        col_mapping = {
            'country': 'Country',
            'Nation': 'Country',
            'nation': 'Country',
            'Effective Size': 'EffectiveSize',
            'effective_size': 'EffectiveSize',
            'constraint': 'Constraint'
        }
        df.rename(columns=col_mapping, inplace=True)

        # Check required columns
        if not all(col in df.columns for col in ['Country', 'EffectiveSize', 'Constraint']):
            continue

        all_years_data[year] = df

        # Count EffectiveSize top 20 frequency (descending)
        effective_top20 = df.sort_values('EffectiveSize', ascending=False).head(20)['Country'].str.strip()
        effective_frequency.update(effective_top20)

        # Count Constraint top 20 frequency (ascending, smaller is better)
        constraint_top20 = df.sort_values('Constraint').head(20)['Country'].str.strip()
        constraint_frequency.update(constraint_top20)

    except Exception:
        continue

# Get top 10 most frequent countries
top10_effective = [c for c, _ in effective_frequency.most_common(10)]
top10_constraint = [c for c, _ in constraint_frequency.most_common(10)]


def calculate_proportion(yearly_data, top_countries, metric):
    """General proportion calculation function"""
    results = []
    for year in sorted(yearly_data.keys()):
        df = yearly_data[year]
        values = {}

        # Get metric value for each country
        for country in top_countries:
            country_data = df[df['Country'].str.strip() == country]
            values[country] = country_data[metric].iloc[0] if not country_data.empty else 0

        # Calculate proportion
        total = sum(values.values())
        for country, value in values.items():
            proportion = round(value / total * 100, 2) if total > 0 else 0
            results.append({'Year': year, 'Country': country, 'Proportion(%)': proportion})

    return pd.DataFrame(results).sort_values(['Year', 'Country']).reset_index(drop=True)


# Calculate EffectiveSize and Constraint proportions
effective_df = calculate_proportion(all_years_data, top10_effective, 'EffectiveSize')
constraint_df = calculate_proportion(all_years_data, top10_constraint, 'Constraint')

# Save results
output_dir = "your_file_location"
os.makedirs(output_dir, exist_ok=True)

effective_output_path = os.path.join(output_dir, "effective_size_top10_frequency_based_2013-2023.csv")
constraint_output_path = os.path.join(output_dir, "constraint_top10_frequency_based_2013-2023.csv")

effective_df.to_csv(effective_output_path, index=False, encoding='utf-8-sig')
constraint_df.to_csv(constraint_output_path, index=False, encoding='utf-8-sig')

# Output summary
print("Processing complete!")
print(f"EffectiveSize results saved to: {effective_output_path} ({len(effective_df)} rows)")
print(f"Constraint results saved to: {constraint_output_path} ({len(constraint_df)} rows)")
print(f"Years processed: {len(all_years_data)}")
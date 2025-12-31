import os
import re
import pandas as pd
import numpy as np
from collections import Counter
import warnings

warnings.filterwarnings('ignore')

# Configuration parameters
file_paths = [
    "your_file_location/2013_betweenness.LOG1.txt",
    "your_file_location/2014_betweenness.LOG2.txt",
    "your_file_location/2015_betweenness.LOG3.txt",
    "your_file_location/2016_betweenness.LOG4.txt",
    "your_file_location/2017_betweenness.LOG5.txt",
    "your_file_location/2018_betweenness.LOG6.txt",
    "your_file_location/2019_betweenness.LOG7.txt",
    "your_file_location/2020_betweenness.LOG8.txt",
    "your_file_location/2021_betweenness.LOG9.txt",
    "your_file_location/2022_betweenness.LOG10.txt",
    "your_file_location/2023_betweenness.LOG11.txt"
]

save_dir = "your_file_location"
os.makedirs(save_dir, exist_ok=True)
output_dir = os.path.join(save_dir, "betweenness_centrality_analysis_results")
os.makedirs(output_dir, exist_ok=True)
years = ['2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023']


def parse_betweenness_file(file_path, year):
    """Parse single year betweenness centrality file"""
    betweenness_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        lines = content.split('\n')
        start_line = -1

        for i, line in enumerate(lines):
            if 'BETWEENNESS CENTRALITY' in line.upper():
                for j in range(i, min(i + 10, len(lines))):
                    if 'Betweenness' in lines[j] and 'nBetweenness' in lines[j]:
                        start_line = j + 1
                        break
                break

        if start_line == -1:
            return betweenness_data

        pattern1 = r'^\s*(\d+)\s+([A-Za-z\s\.\-\'\(\)\/,\?ĂĽĂ´Ă¤Ăˇ]+?)\s+([\d\.]+)\s+([\d\.]+)'
        pattern2 = r'^\s*([A-Za-z\s\.\-\'\(\)\/,\?ĂĽĂ´Ă¤Ăˇ]+?)\s+([\d\.]+)\s+([\d\.]+)'

        for line in lines[start_line:]:
            if not line.strip():
                continue
            if any(key in line for key in
                   ['DESCRIPTIVE STATISTICS', 'Network Centralization', 'Running time:', 'FREEMAN', 'DEGREE']):
                break

            match1 = re.match(pattern1, line)
            match2 = re.match(pattern2, line)

            if match1:
                country_name = match1.group(2).strip()
                n_betweenness = float(match1.group(4))
                betweenness_data[country_name] = n_betweenness
            elif match2:
                country_name = match2.group(1).strip()
                n_betweenness = float(match2.group(3))
                betweenness_data[country_name] = n_betweenness

        return betweenness_data
    except Exception:
        return {}


def get_yearly_top_n(data_dict, years, n=20):
    """Get top N for each year"""
    yearly_top_n = {}
    yearly_values = {}
    yearly_rankings = {}

    for year in years:
        if year in data_dict and data_dict[year]:
            sorted_data = sorted(data_dict[year].items(), key=lambda x: x[1], reverse=True)
            top_n_data = sorted_data[:n]

            yearly_top_n[year] = [c for c, v in top_n_data]
            yearly_values[year] = {c: v for c, v in top_n_data}
            yearly_rankings[year] = {c: i + 1 for i, (c, v) in enumerate(sorted_data)}
        else:
            yearly_top_n[year] = []
            yearly_values[year] = {}
            yearly_rankings[year] = {}

    return yearly_top_n, yearly_values, yearly_rankings


def get_overall_top_n_by_frequency(yearly_top_n, n=20):
    """Get overall top N by frequency"""
    all_countries = []
    for countries in yearly_top_n.values():
        all_countries.extend(countries)
    frequency = Counter(all_countries)
    sorted_freq = sorted(frequency.items(), key=lambda x: (-x[1], x[0]))
    return [c for c, f in sorted_freq[:n]], frequency


def save_results(yearly_values, yearly_rankings, overall_top20, frequency, complete_df, output_dir):
    """Save all results"""
    yearly_top20_df = pd.DataFrame(index=range(1, 21))
    for year in years:
        if year in yearly_values:
            top20 = list(yearly_values[year].keys())[:20]
            formatted = [f"{c} ({v:.6f})" for c, v in yearly_values[year].items()]
            formatted += [""] * (20 - len(formatted))
            yearly_top20_df[year] = formatted
        else:
            yearly_top20_df[year] = [""] * 20

    all_countries = sorted(set(c for yr in yearly_rankings for c in yearly_rankings[yr].keys()))
    detailed_df = pd.DataFrame(index=all_countries, columns=years)
    for c in all_countries:
        for y in years:
            detailed_df.loc[c, y] = yearly_rankings[y].get(c, "")

    overall_df = pd.DataFrame({
        'Rank': range(1, len(overall_top20) + 1),
        'Country': overall_top20,
        'Count': [frequency[c] for c in overall_top20],
        'Frequency': [f"{frequency[c]}/11" for c in overall_top20]
    })

    avg_values = {}
    for c in overall_top20:
        values = [complete_df.loc[y, c] for y in years if
                  c in complete_df.columns and not pd.isna(complete_df.loc[y, c])]
        avg_values[c] = np.mean(values) if values else 0
    sorted_avg = sorted(avg_values.items(), key=lambda x: -x[1])
    avg_df = pd.DataFrame({
        'Rank': range(1, len(sorted_avg) + 1),
        'Country': [c for c, v in sorted_avg],
        'Average': [v for c, v in sorted_avg],
        'Count': [frequency[c] for c, v in sorted_avg]
    })

    betweenness_dir = os.path.join(output_dir, "betweenness_centrality_analysis")
    os.makedirs(betweenness_dir, exist_ok=True)

    yearly_top20_df.to_csv(os.path.join(betweenness_dir, "betweenness_centrality_yearly_top20.csv"),
                           encoding='utf-8-sig')
    detailed_df.to_csv(os.path.join(betweenness_dir, "betweenness_centrality_detailed_rankings.csv"),
                       encoding='utf-8-sig')
    overall_df.to_csv(os.path.join(betweenness_dir, "betweenness_centrality_overall_top20_by_frequency.csv"),
                      encoding='utf-8-sig', index=False)
    avg_df.to_csv(os.path.join(betweenness_dir, "betweenness_centrality_overall_top20_by_average.csv"),
                  encoding='utf-8-sig', index=False)
    complete_df.to_csv(os.path.join(betweenness_dir, "betweenness_centrality_complete_data.csv"), encoding='utf-8-sig')

    with pd.ExcelWriter(os.path.join(betweenness_dir, "betweenness_centrality_complete_data.xlsx"),
                        engine='openpyxl') as writer:
        complete_df.to_excel(writer, sheet_name='Complete_Data')
        overall_df.to_excel(writer, sheet_name='Overall_Rank_Frequency', index=False)
        avg_df.to_excel(writer, sheet_name='Overall_Rank_Average', index=False)

    with pd.ExcelWriter(os.path.join(betweenness_dir, "betweenness_centrality_yearly_top20.xlsx"),
                        engine='openpyxl') as writer:
        yearly_top20_df.to_excel(writer, sheet_name='Yearly_Top20')


def main():
    all_betweenness = {}
    for i, file_path in enumerate(file_paths):
        year = years[i]
        if os.path.exists(file_path):
            all_betweenness[year] = parse_betweenness_file(file_path, year)
        else:
            all_betweenness[year] = {}

    yearly_top20, yearly_values, yearly_rankings = get_yearly_top_n(all_betweenness, years)
    overall_top20, frequency = get_overall_top_n_by_frequency(yearly_top20)

    df_data = {c: [all_betweenness[y].get(c, np.nan) for y in years] for c in overall_top20}
    complete_df = pd.DataFrame(df_data, index=years)

    save_results(yearly_values, yearly_rankings, overall_top20, frequency, complete_df, output_dir)

    with open(os.path.join(output_dir, "betweenness_centrality_analysis_summary.txt"), 'w', encoding='utf-8') as f:
        f.write("Betweenness Centrality Analysis Summary\n")
        f.write(f"Analysis Years: 2013-2023\n")
        f.write("Overall Top 20 (by frequency):\n")
        for i, c in enumerate(overall_top20, 1):
            f.write(f"{i:2d}. {c:25} Count: {frequency[c]}/11\n")

    print("Analysis complete! Results saved to:", output_dir)


if __name__ == "__main__":
    main()
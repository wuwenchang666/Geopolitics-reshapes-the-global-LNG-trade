import os
import re
import pandas as pd
import numpy as np
from collections import Counter
import warnings

warnings.filterwarnings('ignore')

# Configuration parameters
file_paths = [
    "your_file_location/2013_degree.txt",
    "your_file_location/2014_degree.txt",
    "your_file_location/2015_degree.txt",
    "your_file_location/2016_degree.txt",
    "your_file_location/2017_degree.txt",
    "your_file_location/2018_degree.txt",
    "your_file_location/2019_degree.txt",
    "your_file_location/2020_degree.txt",
    "your_file_location/2021_degree.txt",
    "your_file_location/2022_degree.txt",
    "your_file_location/2023_degree.txt"
]

save_dir = "your_file_location"
os.makedirs(save_dir, exist_ok=True)
output_dir = os.path.join(save_dir, "degree_centrality_analysis_results")
os.makedirs(output_dir, exist_ok=True)
years = ['2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023']


def parse_ucinet_file(file_path):
    """Parse UCINET file and extract normalized outdegree/indegree"""
    outdegree_data = {}
    indegree_data = {}

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.read().split('\n')

        in_data_section = False
        pattern = r'^\s*(\d+)\s+([A-Za-z\s\.\-\'\(\)\/,\?ĂĽĂ´Ă¤Ăˇ]+?)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)'

        for line in lines:
            if not line.strip():
                continue

            if 'OutDegree' in line and 'InDegree' in line and 'NrmOutDeg' in line and 'NrmInDeg' in line:
                in_data_section = True
                continue

            if any(key in line for key in ['DESCRIPTIVE STATISTICS', 'Network Centralization', 'Running time:']):
                break

            if in_data_section:
                match = re.match(pattern, line)
                if match:
                    country_name = match.group(2).strip()
                    outdegree_data[country_name] = float(match.group(5))
                    indegree_data[country_name] = float(match.group(6))
                else:
                    parts = line.split()
                    if len(parts) >= 6:
                        try:
                            country_name = ' '.join(parts[:-4]).strip()
                            outdegree_data[country_name] = float(parts[-2])
                            indegree_data[country_name] = float(parts[-1])
                        except (ValueError, IndexError):
                            continue
    except Exception:
        pass

    return outdegree_data, indegree_data


def get_yearly_top_n(data_dict, n=20):
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


def save_analysis_results(data_dict, metric_name, save_dir):
    """Save analysis results"""
    yearly_top20, yearly_values, yearly_rankings = get_yearly_top_n(data_dict)
    overall_top20, frequency = get_overall_top_n_by_frequency(yearly_top20)

    df_data = {c: [data_dict[y].get(c, np.nan) for y in years] for c in overall_top20}
    complete_df = pd.DataFrame(df_data, index=years)

    yearly_top20_df = pd.DataFrame(index=range(1, 21))
    for year in years:
        if year in yearly_values:
            top20 = list(yearly_values[year].keys())[:20]
            formatted = [f"{c} ({v:.3f})" for c, v in yearly_values[year].items()]
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

    os.makedirs(save_dir, exist_ok=True)

    yearly_top20_df.to_csv(os.path.join(save_dir, f"{metric_name}_yearly_top20.csv"), encoding='utf-8-sig')
    detailed_df.to_csv(os.path.join(save_dir, f"{metric_name}_detailed_rankings.csv"), encoding='utf-8-sig')
    overall_df.to_csv(os.path.join(save_dir, f"{metric_name}_overall_top20_by_frequency.csv"), encoding='utf-8-sig', index=False)
    avg_df.to_csv(os.path.join(save_dir, f"{metric_name}_overall_top20_by_average.csv"), encoding='utf-8-sig', index=False)
    complete_df.to_csv(os.path.join(save_dir, f"{metric_name}_complete_data.csv"), encoding='utf-8-sig')

    with pd.ExcelWriter(os.path.join(save_dir, f"{metric_name}_yearly_top20.xlsx"), engine='openpyxl') as writer:
        yearly_top20_df.to_excel(writer, sheet_name='Yearly_Top20')

    with pd.ExcelWriter(os.path.join(save_dir, f"{metric_name}_complete_data.xlsx"), engine='openpyxl') as writer:
        complete_df.to_excel(writer, sheet_name='Complete_Data')
        overall_df.to_excel(writer, sheet_name='Overall_Rank_Frequency', index=False)
        avg_df.to_excel(writer, sheet_name='Overall_Rank_Average', index=False)

    return overall_top20, frequency


def main():
    all_outdegree = {}
    all_indegree = {}

    for i, file_path in enumerate(file_paths):
        year = years[i]
        if os.path.exists(file_path):
            out_data, in_data = parse_ucinet_file(file_path)
            all_outdegree[year] = out_data
            all_indegree[year] = in_data
        else:
            all_outdegree[year] = {}
            all_indegree[year] = {}

    out_dir = os.path.join(output_dir, "outdegree_analysis")
    out_top20, out_freq = save_analysis_results(all_outdegree, "OutDegree", out_dir)

    in_dir = os.path.join(output_dir, "indegree_analysis")
    in_top20, in_freq = save_analysis_results(all_indegree, "InDegree", in_dir)

    with open(os.path.join(output_dir, "analysis_summary.txt"), 'w', encoding='utf-8') as f:
        f.write("Degree Centrality Analysis Summary\n")
        f.write(f"Analysis Years: 2013-2023\n\n")

        f.write("OutDegree Overall Top 20 (by frequency):\n")
        for i, c in enumerate(out_top20, 1):
            f.write(f"{i:2d}. {c:25} Count: {out_freq[c]}/11\n")

        f.write("\nInDegree Overall Top 20 (by frequency):\n")
        for i, c in enumerate(in_top20, 1):
            f.write(f"{i:2d}. {c:25} Count: {in_freq[c]}/11\n")

        common = set(out_top20) & set(in_top20)
        f.write(f"\nCountries appearing in both OutDegree/InDegree Top 20: {len(common)}\n")
        for c in sorted(common):
            f.write(f"  • {c}\n")

    print("Analysis complete! Results saved to:", output_dir)


if __name__ == "__main__":
    main()
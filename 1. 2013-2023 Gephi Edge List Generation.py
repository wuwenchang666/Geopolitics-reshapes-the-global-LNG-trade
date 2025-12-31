import pandas as pd
import numpy as np
from collections import defaultdict
import os


def preprocess_data(file_path, year):
    encodings = ['utf-8-sig', 'utf-8', 'gb2312']
    df = None
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"{year} data read successfully! Encoding: {encoding}")
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        raise ValueError(f"All common encodings failed for {year}. Check file format.")

    print(f"{year} original columns:", df.columns.tolist())
    print(f"{year} original rows:", len(df))

    if 'netWgt' in df.columns:
        df.rename(columns={'netWgt': 'NetWeight'}, inplace=True)
        print(f"{year} field renamed: netWgt -> NetWeight")

    core_fields = ['ReporterName', 'PartnerName', 'NetWeight']
    df.columns = df.columns.str.strip()
    df_core = df[core_fields].copy()

    df_core = df_core.dropna(subset=['NetWeight'])
    df_core = df_core[df_core['NetWeight'] > 0]
    df_core = df_core[df_core['ReporterName'] != df_core['PartnerName']]
    df_core['ReporterName'] = df_core['ReporterName'].str.strip()
    df_core['PartnerName'] = df_core['PartnerName'].str.strip()

    def sort_country_pair(imp_country, exp_country):
        return tuple(sorted([imp_country, exp_country]))

    df_core['sorted_country_pair'] = df_core.apply(
        lambda x: sort_country_pair(x['ReporterName'], x['PartnerName']), axis=1
    )

    print(f"{year} preprocessing done!")
    print(f"{year} valid trade records:", len(df_core))
    print(f"{year} unique countries:", len(set(df_core['ReporterName']) | set(df_core['PartnerName'])))
    return df_core


def calculate_trade_intensity(df_core, year):
    country_total_intensity = defaultdict(float)
    for _, row in df_core.iterrows():
        imp_country = row['ReporterName']
        exp_country = row['PartnerName']
        trade_volume = row['NetWeight']
        country_total_intensity[imp_country] += trade_volume
        country_total_intensity[exp_country] += trade_volume

    pair_co_intensity = defaultdict(float)
    for _, row in df_core.iterrows():
        sorted_pair = row['sorted_country_pair']
        trade_volume = row['NetWeight']
        pair_co_intensity[sorted_pair] += trade_volume

    total_all_country_intensity = sum(country_total_intensity.values())
    total_all_pair_intensity = sum(pair_co_intensity.values())

    print(f"{year} trade intensity calculated.")
    print(f"{year} total country intensity:", round(total_all_country_intensity, 2))
    print(f"{year} total pair intensity:", round(total_all_pair_intensity, 2))
    return country_total_intensity, pair_co_intensity, total_all_country_intensity, total_all_pair_intensity


def calculate_pmi_and_valid_edges(df_core, country_total_intensity, pair_co_intensity,
                                  total_all_country_intensity, total_all_pair_intensity, year):
    all_countries = sorted(list(country_total_intensity.keys()))
    pmi_matrix = pd.DataFrame(
        index=all_countries,
        columns=all_countries,
        dtype=float
    ).fillna(0.0)

    for exp_country in all_countries:
        for imp_country in all_countries:
            if exp_country == imp_country:
                pmi_matrix.loc[exp_country, imp_country] = 0.0
                continue

            sorted_pair = tuple(sorted([imp_country, exp_country]))
            co_intensity = pair_co_intensity.get(sorted_pair, 0.0)

            p_xy = co_intensity / total_all_pair_intensity if total_all_pair_intensity != 0 else 0.0
            p_exp = country_total_intensity[exp_country] / total_all_country_intensity if total_all_country_intensity != 0 else 0.0
            p_imp = country_total_intensity[imp_country] / total_all_country_intensity if total_all_country_intensity != 0 else 0.0

            if p_xy == 0 or p_exp * p_imp == 0:
                pmi_value = 0.0
            else:
                pmi_value = np.log2(p_xy / (p_exp * p_imp))
            pmi_matrix.loc[exp_country, imp_country] = pmi_value

    all_pmi_values = pmi_matrix.values.flatten()
    min_pmi = all_pmi_values.min()
    max_pmi = all_pmi_values.max()
    print(f"{year} PMI calculated. Range: Min={min_pmi:.4f}, Max={max_pmi:.4f}")

    valid_edge_list = []
    for _, row in df_core.iterrows():
        source_exp = row['PartnerName']
        target_imp = row['ReporterName']
        trade_volume = row['NetWeight']
        pmi_value = pmi_matrix.loc[source_exp, target_imp]

        if max_pmi == min_pmi:
            wij_value = 0.0
        else:
            wij_value = (pmi_value - min_pmi) / (max_pmi - min_pmi)
        wij_value = round(wij_value, 4)

        valid_edge_list.append({
            'source': source_exp,
            'target': target_imp,
            'weight': wij_value,
            'raw_pmi': round(pmi_value, 4),
            'trade_volume': trade_volume
        })

    valid_edge_df = pd.DataFrame(valid_edge_list).drop_duplicates(
        subset=['source', 'target']
    )

    print(f"{year} valid edge table generated.")
    print(f"{year} valid edges (deduplicated):", len(valid_edge_df))
    return pmi_matrix, valid_edge_df


def export_results(pmi_matrix, valid_edge_df, output_dir, year):
    pmi_matrix_path = os.path.join(output_dir, f"{year}_Raw_PMI_Matrix.csv")
    valid_edge_path = os.path.join(output_dir, f"{year}_Wij_Valid_Trade_Edges.csv")

    pmi_matrix.to_csv(pmi_matrix_path, encoding='utf-8-sig', index=True)
    valid_edge_df.to_csv(valid_edge_path, encoding='utf-8-sig', index=False)

    print(f"{year} results exported to: {output_dir}")
    print(f"  - PMI matrix: {os.path.basename(pmi_matrix_path)}")
    print(f"  - Gephi edge table: {os.path.basename(valid_edge_path)}")


def main():
    data_config = [
        (2013, "your_file_location/2013_data.csv"),
        (2014, "your_file_location/2014_data.csv"),
        (2015, "your_file_location/2015_data.csv"),
        (2016, "your_file_location/2016_data.csv"),
        (2017, "your_file_location/2017_data.csv"),
        (2018, "your_file_location/2018_data.csv"),
        (2019, "your_file_location/2019_data.csv"),
        (2020, "your_file_location/2020_data.csv"),
        (2021, "your_file_location/2021_data.csv"),
        (2022, "your_file_location/2022_data.csv"),
        (2023, "your_file_location/2023_data.csv")
    ]

    for year, file_path in data_config:
        print("=" * 60)
        print(f"Processing {year} trade data")
        print("=" * 60)

        df_valid_trade = preprocess_data(file_path, year)

        country_intensity, pair_intensity, total_country_intensity, total_pair_intensity = calculate_trade_intensity(df_valid_trade, year)

        pmi_matrix, valid_edge_df = calculate_pmi_and_valid_edges(
            df_valid_trade,
            country_intensity,
            pair_intensity,
            total_country_intensity,
            total_pair_intensity,
            year
        )

        output_dir = os.path.dirname(file_path)
        export_results(pmi_matrix, valid_edge_df, output_dir, year)

        print(f"{year} edge table preview (first 3):")
        print(valid_edge_df[['source', 'target', 'weight', 'trade_volume']].head(3))
        print(f"{year} processing complete.\n")

    print("=" * 60)
    print("2013-2023 batch processing finished!")
    print("Edge tables saved in the same directory as source files, ready for Gephi.")
    print("=" * 60)


if __name__ == "__main__":
    main()
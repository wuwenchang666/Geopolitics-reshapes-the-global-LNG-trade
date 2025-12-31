import pandas as pd
import numpy as np
import networkx as nx
import os


def calculate_structural_holes(adj_matrix_path, direction='both'):
    """
    Calculate structural hole indicators for trade network

    Parameters:
        adj_matrix_path: Path to adjacency matrix CSV file
        direction: Relationship direction, options: 'outgoing', 'incoming', 'both'

    Returns:
        DataFrame containing structural hole indicators
    """
    print(f"Calculating structural hole indicators, direction: {direction}")

    # Read adjacency matrix
    df_matrix = pd.read_csv(adj_matrix_path, index_col=0, encoding='utf-8')
    countries = df_matrix.index.tolist()
    n = len(countries)

    print(f"Loaded adjacency matrix with {n} countries")

    # Adjust matrix based on direction
    if direction == 'outgoing':
        matrix = df_matrix.values.copy()
    elif direction == 'incoming':
        matrix = df_matrix.T.values.copy()
    elif direction == 'both':
        matrix = (df_matrix.values + df_matrix.T.values) / 2
        np.fill_diagonal(matrix, 0)

    # Convert to NetworkX graph object
    G = nx.DiGraph() if direction != 'both' else nx.Graph()
    G.add_nodes_from(countries)

    # Add weighted edges
    edge_count = 0
    for i in range(n):
        for j in range(n):
            if i != j and matrix[i, j] > 0:
                G.add_edge(countries[i], countries[j], weight=matrix[i, j])
                edge_count += 1

    print(f"Built network graph with {edge_count} edges")

    # Check for isolated nodes
    isolated_nodes = [node for node in countries if G.degree(node) == 0]
    if isolated_nodes:
        print(f"Found {len(isolated_nodes)} isolated nodes")

    # Calculate structural hole indicators
    results = []

    for node in countries:
        neighbors = list(G.neighbors(node))

        if len(neighbors) == 0:
            results.append({
                'Country': node,
                'Degree': 0,
                'EffectiveSize': np.nan,
                'Efficiency': np.nan,
                'Constraint': np.nan,
                'Hierarchy': np.nan
            })
            continue

        total_weight = sum([G[node][j]['weight'] for j in neighbors])

        if total_weight == 0:
            results.append({
                'Country': node,
                'Degree': len(neighbors),
                'EffectiveSize': 0,
                'Efficiency': 0,
                'Constraint': np.nan,
                'Hierarchy': np.nan
            })
            continue

        # Calculate p_ij matrix
        p_ij = {}
        for j in neighbors:
            p_ij[j] = G[node][j]['weight'] / total_weight

        # Calculate constraint
        constraint = 0
        for j in neighbors:
            direct = p_ij[j]

            indirect = 0
            for q in neighbors:
                if q != j:
                    if G.has_edge(q, j):
                        neighbors_q = list(G.neighbors(q))
                        total_weight_q = sum([G[q][k]['weight'] for k in neighbors_q])
                        if total_weight_q > 0:
                            p_qj = G[q][j]['weight'] / total_weight_q
                        else:
                            p_qj = 0
                    else:
                        p_qj = 0

                    indirect += p_ij[q] * p_qj

            constraint += (direct + indirect) ** 2

        # Calculate effective size
        effective_size = 0
        for j in neighbors:
            redundancy = 0
            for q in neighbors:
                if q != j:
                    if G.has_edge(j, q) or G.has_edge(q, j):
                        redundancy += 1

            if len(neighbors) > 0:
                effective_size += 1 - (redundancy / len(neighbors))

        # Calculate efficiency
        efficiency = effective_size / len(neighbors) if len(neighbors) > 0 else 0

        # Calculate hierarchy
        hierarchy = 0
        valid_pairs = 0

        for j in neighbors:
            direct = p_ij[j]
            indirect = 0
            for q in neighbors:
                if q != j:
                    if G.has_edge(q, j):
                        neighbors_q = list(G.neighbors(q))
                        total_weight_q = sum([G[q][k]['weight'] for k in neighbors_q])
                        if total_weight_q > 0:
                            p_qj = G[q][j]['weight'] / total_weight_q
                        else:
                            p_qj = 0
                        indirect += p_ij[q] * p_qj

            c_ij = (direct + indirect) ** 2

            if constraint > 0 and c_ij > 0:
                ratio = c_ij / constraint
                if ratio > 0:
                    hierarchy += ratio * np.log(ratio)
                    valid_pairs += 1

        if valid_pairs > 1 and constraint > 0 and hierarchy < 0:
            n_valid = valid_pairs
            hierarchy = -hierarchy / (n_valid * np.log(n_valid))
        else:
            hierarchy = np.nan

        results.append({
            'Country': node,
            'Degree': len(neighbors),
            'EffectiveSize': round(effective_size, 4),
            'Efficiency': round(efficiency, 4),
            'Constraint': round(constraint, 4) if not np.isnan(constraint) else np.nan,
            'Hierarchy': round(hierarchy, 4) if not np.isnan(hierarchy) else np.nan
        })

    results_df = pd.DataFrame(results)

    results_df_for_sort = results_df.copy()
    results_df_for_sort['Constraint'] = results_df_for_sort['Constraint'].fillna(999)
    results_df_for_sort = results_df_for_sort.sort_values('Constraint', ascending=True)

    results_df = results_df.loc[results_df_for_sort.index].reset_index(drop=True)
    results_df['Constraint_Rank'] = range(1, len(results_df) + 1)

    results_df['EffectiveSize_Rank'] = results_df['EffectiveSize'].rank(
        ascending=False, method='min', na_option='bottom'
    ).astype(int)

    return results_df


def batch_structural_holes_analysis(base_dir, start_year=2013, end_year=2023):
    """
    Batch analyze structural holes for multiple years

    Parameters:
        base_dir: Base directory, e.g., "your_file_location"
        start_year: Start year
        end_year: End year
    """
    print("=" * 60)
    print(f"Batch Structural Holes Analysis Tool ({start_year}-{end_year})")
    print("=" * 60)

    summary_data = []

    for year in range(start_year, end_year + 1):
        print(f"\nProcessing {year} data...")

        adj_matrix_file = os.path.join(base_dir, str(year),
                                       f"Trade_Weighted_Adjacency_Matrix_{year}.csv")

        if not os.path.exists(adj_matrix_file):
            print(f"File does not exist: {adj_matrix_file}")
            print(f"Please ensure the edge-to-adjacency matrix conversion has been run")
            continue

        try:
            for direction in ['outgoing', 'incoming', 'both']:
                print(f"Calculating direction: {direction}")

                results_df = calculate_structural_holes(adj_matrix_file, direction=direction)

                output_file = os.path.join(base_dir, str(year),
                                           f"Structural_Holes_{direction}_{year}.csv")
                results_df.to_csv(output_file, encoding='utf-8', index=False)

                print(f"Results saved to: {output_file}")

                valid_results = results_df[results_df['Constraint'].notna()]
                if len(valid_results) > 0:
                    top_countries = valid_results.head(10)
                    print(f"\n{direction.capitalize()} - Top 10 countries with rich structural holes:")
                    print("-" * 80)
                    print(
                        top_countries[['Country', 'Constraint', 'EffectiveSize', 'Efficiency']].to_string(index=False))

                    summary_data.append({
                        'Year': year,
                        'Direction': direction,
                        'Top_Country': top_countries.iloc[0]['Country'],
                        'Min_Constraint': top_countries.iloc[0]['Constraint'],
                        'Avg_Constraint': valid_results['Constraint'].mean(),
                        'Num_Countries': len(results_df),
                        'Num_Valid': len(valid_results),
                        'File_Path': output_file
                    })
                else:
                    print(f"No valid structural hole calculation results")

        except Exception as e:
            print(f"Processing failed: {str(e)}")
            import traceback
            print(f"Error details: {traceback.format_exc()}")

    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_file = os.path.join(base_dir, "Structural_Holes_Summary_2013_2023.csv")
        summary_df.to_csv(summary_file, encoding='utf-8', index=False)
        print(f"\nSummary report saved to: {summary_file}")

        print("\nAnalysis complete! Summary results:")
        print("=" * 60)
        for direction in ['outgoing', 'incoming', 'both']:
            dir_data = summary_df[summary_df['Direction'] == direction]
            if len(dir_data) > 0:
                print(f"\nDirection: {direction.upper()}")
                print(dir_data[['Year', 'Top_Country', 'Min_Constraint', 'Avg_Constraint']].to_string(index=False))

    print("\n" + "=" * 60)
    print("Batch analysis complete!")
    print("=" * 60)


def analyze_single_year(year, base_dir="your_file_location", direction='both'):
    """
    Analyze structural holes for a single year
    """
    print(f"Analyzing structural hole data for {year}...")

    adj_matrix_file = os.path.join(base_dir, str(year),
                                   f"Trade_Weighted_Adjacency_Matrix_{year}.csv")

    if not os.path.exists(adj_matrix_file):
        print(f"File does not exist: {adj_matrix_file}")
        return None

    results_df = calculate_structural_holes(adj_matrix_file, direction=direction)

    output_file = os.path.join(base_dir, str(year),
                               f"Structural_Holes_{direction}_{year}.csv")
    results_df.to_csv(output_file, encoding='utf-8', index=False)

    print(f"Results saved to: {output_file}")

    print(f"\n{year} {direction} direction complete results:")
    print("=" * 80)
    print(results_df.head(20).to_string(index=False))

    valid_results = results_df[results_df['Constraint'].notna()]
    print(f"\nStatistics:")
    print(f"   Total countries: {len(results_df)}")
    print(f"   Valid results: {len(valid_results)}")
    print(f"   Constraint range: {valid_results['Constraint'].min():.4f} - {valid_results['Constraint'].max():.4f}")
    print(f"   Average constraint: {valid_results['Constraint'].mean():.4f}")

    return results_df


if __name__ == "__main__":
    BASE_DATA_DIR = "your_file_location"

    print("=" * 70)
    print("Trade Network Structural Holes Analysis System (2013-2023)")
    print("=" * 70)

    print("\nPlease select analysis mode:")
    print("1. Batch analyze all years (2013-2023)")
    print("2. Analyze a single year")
    print("3. Test mode (analyze 2013 only)")

    choice = input("\nEnter choice (1/2/3): ").strip()

    if choice == "1":
        batch_structural_holes_analysis(BASE_DATA_DIR, 2013, 2023)

    elif choice == "2":
        year = int(input("Enter year to analyze (2013-2023): ").strip())
        direction = input("Enter analysis direction (outgoing/incoming/both, default both): ").strip()
        direction = direction if direction in ['outgoing', 'incoming', 'both'] else 'both'

        if 2013 <= year <= 2023:
            analyze_single_year(year, BASE_DATA_DIR, direction)
        else:
            print("Year must be between 2013-2023")

    elif choice == "3":
        print("\nTest mode: Analyzing 2013 bidirectional relationships")
        results = analyze_single_year(2013, BASE_DATA_DIR, 'both')

        if results is not None:
            test_summary = results.head(20)[['Country', 'Constraint', 'EffectiveSize', 'Constraint_Rank']]
            test_summary_path = os.path.join(BASE_DATA_DIR, "structural_holes_test_results_2013.csv")
            test_summary.to_csv(test_summary_path, encoding='utf-8', index=False)
            print(f"\nTest summary saved to: {test_summary_path}")

    else:
        print("Invalid choice, program exiting")
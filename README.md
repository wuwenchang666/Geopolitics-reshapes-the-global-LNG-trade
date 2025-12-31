# Geopolitics-reshapes-the-global-LNG-trade
The code files process the raw data to generate network structures and perform statistical analyses.
## 1. 2013-2023 Gephi Edge List Generation
**Function**: Processes the original data from the submitted dataset by year.
**Method**: Calculates the Pointwise Mutual Information (PMI) values. Negative PMI values are processed to derive the W<sub>ij</sub> weighted edge lists.
**Output**: Generates files suitable for import into Gephi.
**Usage**: These results are used in Gephi to visualize the trade dependency networks and perform community detection plotting.

## 2. 2013-2023 Ucinet Adjacency Matrix Data
**Function**: Transforms the edge list format into adjacency matrices compatible with Ucinet software.
**Usage**: Facilitates the calculation of network metrics, specifically Betweenness Centrality and Degree Centrality, within the Ucinet environment.

## 3. 2013-2023 Structural Hole Analysis
**Function**: Performs structural hole analysis on the adjacency matrices generated in step (2).
**Metrics**: Calculates key indicators such as "Constraint" and "Effective Size" to measure the structural holes of nodes in the network.

## 4. Structure Hole Top 10
**Function**: Statistical aggregation of structural hole results.
**Method**: Counts the frequency of the top 20 countries identified in the "2013-2023 structure hole analyse" step to determine the overall Top 10 countries.
**Correlation**: Corresponds to the data presented in Table 1 and Table 2 of the manuscript.

## 5. Point Indegree and Outdegree Top 20
**Function**: Statistical aggregation of Degree Centrality results.
**Method**: Based on Ucinet analysis, counts the frequency of the top-ranking countries to identify the overall Top 20 countries for both in-degree and out-degree.

## 6. Betweenness Centrality Top 10
**Function**: Statistical aggregation of Betweenness Centrality results.
**Method**: Based on Ucinet analysis, counts the frequency of the top-ranking countries to identify the overall Top 10 countries with the highest bridging roles.

## 7-9. Data Reshaping for Origin (Point Outdegree/Indegree/Betweenness Centrality import to origin)
**Function**: Data formatting for visualization.
**Method**: Converts the aggregated results of the Top 20 and Top 10 countries (from steps 5 and 6) into a "long format" (tidy data).
**Usage**: These files are optimized for import into OriginLab to generate heatmaps for Out-degree, In-degree, and Betweenness Centrality.

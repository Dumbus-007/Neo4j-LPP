# Ljubljana Transit Graph & Random Walk Simulation

This project models the Ljubljana Public Transport (LPP) network as a weighted graph in Neo4j and performs random walk simulations to analyze network connectivity and passenger meeting points.

## Dependencies

To run the data processing and simulation scripts, you will need:
- **Python 3.7+**
- **Neo4j Database** (Local or Remote)
- **Python Libraries**:
  ```bash
  pip install neo4j pandas matplotlib
  ```

---

## Project Structure

### Data Processing
- **`lpp_gtfs/`**: Contains the raw GTFS text files (stops, stop_times, calendar, etc.) NOT INCLUDED IN THIS REPOSITORY, can be downloaded from [GTFSrt.si](https://rt.gtfs.si/).
- **`generate_graph_data.py`**: The primary ETL script. It calculates travel times and wait penalties, generates walking edges between stops (threshold 300m), and exports Neo4j-ready CSVs.
- **`neo4j_lpp/`**:
  - `neo4j_stops.csv`: Processed stop nodes with GPS coordinates.
  - `neo4j_edges.csv`: Bus trip relationships with time-cost weights.
  - `neo4j_walk_edges.csv`: Walking transfer relationships.
  - **`load_graph.cypher`**: Cypher script to import the above CSVs into Neo4j.

### Simulation & Analysis
- **`simulate_meeting.py`**: A Python script that connects to Neo4j and simulates two random walkers moving through the network. It calculates transition probabilities inversely proportional to edge weights (time).
- **`simulation_results.csv`**: The raw output of the latest simulation run (start nodes, meeting time, and meeting hub).
- **`analyze_results.ipynb`**: (New) A Jupyter notebook to visualize and summarize the simulation findings.

### Documentation
- **`README.md`**: Project overview and documentation.
- **`project_journal.md`**: A chronological log of project steps and decisions.

---

## Graph Architecture & Weight Logic

All weights represent **Time Cost in Seconds**.

### 1. Bus Edges (`:BUS`)
$$Weight = \text{Avg Travel Time} + \text{Wait Penalty}$$
- **Wait Penalty**: Based on an 18-hour service window. $Weight_{wait} = 64800 / (2 \times \text{Trips})$.

### 2. Walking Edges (`:WALK`)
$$Weight = \frac{\text{Distance (m)}}{1.4 \text{ m/s}}$$
- Generated for all stop pairs within **300 meters**.

---

## Getting Started

1.  **Generate Data**: Run `python generate_graph_data.py`.
2.  **Import to Neo4j**: Open Neo4j and run the queries in `Neo4j-LPP/load_graph.cypher`.
3.  **Run Simulation**: Update credentials in `simulate_meeting.py` and run it.
4.  **Analyze**: Open `analyze_results.ipynb` to view the hubs and statistics.

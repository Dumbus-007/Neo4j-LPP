# Ljubljana Transit Graph & Random Walk Simulation

This project models the Ljubljana Public Transport (LPP) network as a weighted graph in Neo4j and performs random walk simulations to analyze network connectivity and passenger meeting points.

## Dependencies

To run the data processing and simulation scripts, you will need:
- **Python 3.7+**
- **Neo4j Database** (Local or Remote) with **Graph Data Science (GDS)** library installed.
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
- **`simulate_meeting_gds.py`**: (New) An optimized version of the simulation that runs entirely within the Neo4j database using the GDS library. It stores meeting results as persistent nodes in the graph.
- **`simulation_results.csv`**: The raw output of the latest Python-based simulation run.
- **`analyze_results.ipynb`**: A Jupyter notebook to visualize and summarize the simulation findings.

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

1.  **Prepare Data**: Ensure your GTFS data is in a folder named `lpp_gtfs` in the parent directory of this repository.
2.  **Generate Data**: Run `python generate_graph_data.py`. This will create a `neo4j_lpp` folder with the output CSVs.
3.  **Import to Neo4j**: 
    - Copy the CSVs from `neo4j_lpp/` into your Neo4j instance's **`import/`** folder.
    - Run the queries in `neo4j_lpp/load_graph.cypher`.
4.  **Run Simulation**:
    - **Option A (Python)**: Update credentials in `simulate_meeting.py` and run it. Results are saved to `simulation_results.csv`.
    - **Option B (Neo4j GDS - Recommended)**: Update credentials in `simulate_meeting_gds.py` and run it. This version is faster and stores results directly in the database as `:SimulationResult` nodes.
5.  **Analyze**: Open `analyze_results.ipynb` to view the hubs and statistics.


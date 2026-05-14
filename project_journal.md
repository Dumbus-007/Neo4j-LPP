# Project Journal: progress tracker

### Data preparation (1h)

Prepare data in the right format to populate neo4j database. (done)

### Creating graph in Neo4j (1h + 2h)

Create graph in Neo4j. (done)
905 nodes, 1064 relationships.

- Fix error in graph logic: either add walking edges or merge nodes that are pairs/ within walking distance. 

Redesigned weights to reflect travel and waiting times to accommodate for walking distance edges.

### Simulate two random walks on the graph (1h)

- Figure out how to run simulations on it. (done)
- write code for the simulation in Python. (done)
- collect data from simulations: descrete meeting time, starting nodes, finishing node. (done)

### Analysis and Documentation (1h)

- Update README with project overview and dependencies. (done)
- Create Jupyter Notebook (`analyze_results.ipynb`) for visualization. (done)

### Optimize Simulation with Neo4j GDS (1h)

- Explore if Cypher/GDS can handle the random walk meeting logic. (done)
- Implement `inv_weight` logic for biased walks in Cypher. (done)
- Write `simulate_meeting_gds.py` to automate graph projection and simulation. (done)
- Store results as `:SimulationResult` nodes for persistence. (done)

### Next steps

- Explore deeper network metrics (Centrality, PageRank).
- Compare results with teorethical bounds for meeting times.
- Additional questions: furthest nodes from each other, most connected nodes, etc.

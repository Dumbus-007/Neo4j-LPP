import os
from neo4j import GraphDatabase

# --- CONFIGURATION ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "[PASSWORD]"  # Update this with your actual password
GRAPH_NAME = "transitGraph"
NUM_RUNS = 1000
WALK_LENGTH = 5000
# ---------------------

class GDSTransitSimulation:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, description):
        print(f"Executing: {description}...")
        try:
            with self.driver.session() as session:
                result = session.run(query)
                return list(result)
        except Exception as e:
            print(f"Error during '{description}': {e}")
            return []

    def setup_weights(self):
        query = """
        MATCH ()-[r:BUS|WALK]->()
        SET r.inv_weight = 1.0 / r.weight
        """
        self.run_query(query, "Calculating inverse weights")

    def project_graph(self):
        # Drop existing graph if it exists
        drop_query = f"CALL gds.graph.drop('{GRAPH_NAME}', false) YIELD graphName"
        self.run_query(drop_query, "Cleaning up old projection")

        # Create new projection
        project_query = f"""
        CALL gds.graph.project(
          '{GRAPH_NAME}',
          'Stop',
          {{
            BUS: {{ orientation: 'NATURAL', properties: 'inv_weight' }},
            WALK: {{ orientation: 'UNDIRECTED', properties: 'inv_weight' }}
          }}
        )
        """
        self.run_query(project_query, f"Projecting graph '{GRAPH_NAME}' into GDS")

    def run_simulation(self):
        # This query runs the simulation and saves results to SimulationResult nodes
        query = f"""
        MATCH (s:Stop)
        WITH collect(id(s)) AS stopIds
        UNWIND range(1, {NUM_RUNS}) AS runId
        WITH runId, 
             stopIds[toInteger(rand()*size(stopIds))] AS startA,
             stopIds[toInteger(rand()*size(stopIds))] AS startB

        CALL gds.randomWalk.stream('{GRAPH_NAME}', {{
          sourceNodes: [startA, startB],
          walkLength: {WALK_LENGTH},
          walksPerNode: 1,
          relationshipWeightProperty: 'inv_weight'
        }})
        YIELD nodeIds

        WITH runId, collect(nodeIds) AS paths
        WITH runId, paths[0] AS w1, paths[1] AS w2

        UNWIND range(1, size(w1)-1) AS step
        WITH runId, step, w1[step] AS nodeA, w2[step] AS nodeB
        WHERE nodeA = nodeB
        WITH runId, min(step) AS meetingStep, nodeA AS meetingNodeId

        MATCH (m:Stop) WHERE id(m) = meetingNodeId
        MERGE (res:SimulationResult {{runId: runId}})
        SET res.meetingStep = meetingStep,
            res.meetingNode = m.name,
            res.timestamp = datetime()
        RETURN count(*) AS savedCount
        """
        self.run_query(query, f"Running {NUM_RUNS} simulation runs")

    def show_summary(self):
        query = """
        MATCH (r:SimulationResult)
        RETURN 
            count(*) AS totalMeetings,
            avg(r.meetingStep) AS avgStep,
            min(r.meetingStep) AS minStep,
            max(r.meetingStep) AS maxStep
        """
        results = self.run_query(query, "Fetching summary statistics")
        if results:
            res = results[0]
            print("\n--- Simulation Summary (GDS) ---")
            print(f"Total Successful Meetings: {res['totalMeetings']}")
            if res['totalMeetings'] > 0:
                print(f"Average Meeting Step:     {res['avgStep']:.2f}")
                print(f"Quickest Meeting:         {res['minStep']} steps")
                print(f"Slowest Meeting:          {res['maxStep']} steps")

        query = """
        MATCH (r:SimulationResult)
        RETURN r.meetingNode AS Hub, count(*) AS count
        ORDER BY count DESC
        LIMIT 5
        """
        hubs = self.run_query(query, "Fetching top meeting hubs")
        if hubs:
            print("\nTop 5 Meeting Hubs:")
            for record in hubs:
                print(f"  {record['count']:3} times: {record['Hub']}")

def main():
    sim = GDSTransitSimulation(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        sim.setup_weights()
        sim.project_graph()
        sim.run_simulation()
        sim.show_summary()
    finally:
        sim.close()

if __name__ == "__main__":
    main()

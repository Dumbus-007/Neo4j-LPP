import random
import csv
import os
from collections import defaultdict
from neo4j import GraphDatabase

# --- CONFIGURATION ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "[PASSWORD]"
MAX_STEPS = 5000  # Increased from 1000
# ---------------------

class TransitSimulation:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.adj = defaultdict(list)
        self.all_stops = []
        self.stop_names = {}  # stop_id -> stop_name

    def close(self):
        self.driver.close()

    def load_graph_from_db(self):
        """Fetches the graph structure, weights, and names from Neo4j."""
        print(f"Connecting to Neo4j at {NEO4J_URI}...")
        try:
            with self.driver.session() as session:
                # 1. Fetch all stops and their names
                print("Fetching stops and names...")
                stops_result = session.run("MATCH (s:Stop) RETURN s.stop_id AS stop_id, s.name AS name")
                for record in stops_result:
                    sid = record["stop_id"]
                    self.all_stops.append(sid)
                    self.stop_names[sid] = record["name"]
                
                if not self.all_stops:
                    print("Warning: No stops found in the database.")
                    return

                # 2. Fetch all relationships (BUS and WALK)
                print("Fetching relationships and calculating probabilities...")
                edges_result = session.run("""
                    MATCH (a:Stop)-[r:BUS|WALK]->(b:Stop)
                    RETURN a.stop_id AS src, b.stop_id AS tgt, r.weight AS weight
                """)
                
                raw_edges = defaultdict(list)
                for record in edges_result:
                    src, tgt, weight = record["src"], record["tgt"], record["weight"]
                    if weight > 0:
                        raw_edges[src].append((tgt, 1.0 / weight))
                
                # 3. Normalize to probabilities
                for src, neighbors in raw_edges.items():
                    total_inv_weight = sum(inv_w for _, inv_w in neighbors)
                    for tgt, inv_w in neighbors:
                        self.adj[src].append((tgt, inv_w / total_inv_weight))
            
            print(f"Graph loaded: {len(self.all_stops)} nodes, {sum(len(v) for v in self.adj.values())} edges.")
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")

    def simulate_one_run(self, max_steps=MAX_STEPS):
        if not self.all_stops:
            return None

        start_a = random.choice(self.all_stops)
        start_b = random.choice(self.all_stops)
        
        pos_a = start_a
        pos_b = start_b
        
        for step in range(1, max_steps + 1):
            if pos_a == pos_b:
                return [
                    start_a, self.stop_names.get(start_a, "Unknown"),
                    start_b, self.stop_names.get(start_b, "Unknown"),
                    step - 1, 
                    pos_a, self.stop_names.get(pos_a, "Unknown")
                ]
            
            if pos_a in self.adj:
                neighbors, probs = zip(*self.adj[pos_a])
                pos_a = random.choices(neighbors, weights=probs)[0]
            
            if pos_b in self.adj:
                neighbors, probs = zip(*self.adj[pos_b])
                pos_b = random.choices(neighbors, weights=probs)[0]
                
        if pos_a == pos_b:
            return [
                start_a, self.stop_names.get(start_a, "Unknown"),
                start_b, self.stop_names.get(start_b, "Unknown"),
                max_steps, 
                pos_a, self.stop_names.get(pos_a, "Unknown")
            ]
            
        return [
            start_a, self.stop_names.get(start_a, "Unknown"),
            start_b, self.stop_names.get(start_b, "Unknown"),
            max_steps + 1, 
            "TIMEOUT", "TIMEOUT"
        ]

def main():
    sim = TransitSimulation(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    sim.load_graph_from_db()
    
    if not sim.all_stops:
        sim.close()
        return

    num_runs = 1000
    results = []
    
    print(f"\nStarting {num_runs} simulation runs (Max {MAX_STEPS} steps each)...")
    for i in range(num_runs):
        if i % 100 == 0 and i > 0:
            print(f"   Completed {i} runs...")
        run_data = sim.simulate_one_run()
        if run_data:
            results.append(run_data)
        
    sim.close()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "simulation_results.csv")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "start_id_a", "start_name_a", 
            "start_id_b", "start_name_b", 
            "meeting_step", 
            "meeting_id", "meeting_name"
        ])
        writer.writerows(results)
        
    meetings = [r for r in results if r[5] != "TIMEOUT"]
    meeting_count = len(meetings)
    if meeting_count > 0:
        avg_time = sum(m[4] for m in meetings) / meeting_count
        print(f"\nSummary Results (Max {MAX_STEPS} steps):")
        print(f"- Successful Meetings: {meeting_count}/{num_runs} ({meeting_count/num_runs*100:.1f}%)")
        print(f"- Average Meeting Time: {avg_time:.2f} steps")
        
        meeting_hubs = defaultdict(int)
        for m in meetings:
            meeting_hubs[(m[5], m[6])] += 1
        
        # Sort by frequency
        sorted_hubs = sorted(meeting_hubs.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\nTop 5 Meeting Hubs:")
        for (sid, sname), count in sorted_hubs[:5]:
            print(f"  {count:3} times: {sname} ({sid})")
    else:
        print(f"\nSummary Results: No meetings occurred within {MAX_STEPS} steps.")

    print(f"\nDetailed results saved to: {output_path}")

if __name__ == "__main__":
    main()



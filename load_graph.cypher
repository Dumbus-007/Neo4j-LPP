// ==========================================
// 1. Create Constraints
// ==========================================
// It's critical to create a uniqueness constraint on the stop_id before loading data.
// This ensures nodes are unique and drastically speeds up relationship creation.

CREATE CONSTRAINT stop_id_unique IF NOT EXISTS FOR (s:Stop) REQUIRE s.stop_id IS UNIQUE;

// Wait for the index/constraint to populate before running the next queries.


// ==========================================
// 2. Load Stops (Nodes)
// ==========================================
// Note: If you have placed the CSVs in the Neo4j "import" folder, use 'file:///neo4j_stops.csv'.
// If you are loading directly from your desktop and have enabled file imports in your neo4j.conf,
// use the absolute path: 'file:///c:/Users/Lara/Desktop/DELO/Challenge/Neo4j-LPP/neo4j_stops.csv'

LOAD CSV WITH HEADERS FROM 'file:///c:/Users/Lara/Desktop/DELO/Challenge/Neo4j-LPP/neo4j_stops.csv' AS row
MERGE (s:Stop {stop_id: row.stop_id})
SET s.name = row.name;


// ==========================================
// 3. Load Connections (Relationships)
// ==========================================
// This query creates a directed :ROUTES_TO relationship with the aggregated weight.

LOAD CSV WITH HEADERS FROM 'file:///c:/Users/Lara/Desktop/DELO/Challenge/Neo4j-LPP/neo4j_edges.csv' AS row
MATCH (source:Stop {stop_id: row.source_stop_id})
MATCH (target:Stop {stop_id: row.target_stop_id})
MERGE (source)-[r:ROUTES_TO]->(target)
SET r.weight = toInteger(row.weight);

// ==========================================
// 4. Verify Data
// ==========================================
// Run this to see a small sample of the graph you just built:
// MATCH p=()-[r:ROUTES_TO]->() RETURN p LIMIT 50;

// ==========================================
// 1. Create Constraints
// ==========================================
CREATE CONSTRAINT stop_id_unique IF NOT EXISTS FOR (s:Stop) REQUIRE s.stop_id IS UNIQUE;

// ==========================================
// 2. Load Stops (Nodes)
// ==========================================
LOAD CSV WITH HEADERS FROM 'file:///neo4j_stops.csv' AS row
MERGE (s:Stop {stop_id: row.stop_id})
SET s.name = row.name,
    s.lat = toFloat(row.lat),
    s.lon = toFloat(row.lon);

// ==========================================
// 3. Load Bus Connections (Relationships)
// ==========================================
LOAD CSV WITH HEADERS FROM 'file:///neo4j_edges.csv' AS row
MATCH (source:Stop {stop_id: row.source_stop_id})
MATCH (target:Stop {stop_id: row.target_stop_id})
MERGE (source)-[r:BUS]->(target)
SET r.weight = toFloat(row.weight);

// ==========================================
// 4. Load Walk Connections (Relationships)
// ==========================================
LOAD CSV WITH HEADERS FROM 'file:///neo4j_walk_edges.csv' AS row
MATCH (source:Stop {stop_id: row.source_stop_id})
MATCH (target:Stop {stop_id: row.target_stop_id})
MERGE (source)-[r:WALK]->(target)
SET r.weight = toFloat(row.weight);

// ==========================================
// 5. Verify Data
// ==========================================
// Check total nodes
// MATCH (n:Stop) RETURN count(n);

// Check total relationships by type
// MATCH ()-[r]->() RETURN type(r), count(r);

// Sample graph view:
// MATCH p=(:Stop)-[:BUS|WALK]->(:Stop) RETURN p LIMIT 50;

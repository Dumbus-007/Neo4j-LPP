import csv
import os
import math
from collections import defaultdict
from datetime import datetime

def haversine(lat1, lon1, lat2, lon2):
    """Calculates the distance in meters between two GPS coordinates."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def time_to_seconds(time_str):
    """Converts HH:MM:SS string to seconds (handles times > 24:00:00)."""
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s

def generate_neo4j_data():
    # Relative paths:
    # Assumes gtfs data is in a folder 'lpp_gtfs' in the parent directory
    # and output will go into 'neo4j_lpp' in the current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gtfs_dir = os.path.join(script_dir, "..", "lpp_gtfs")
    neo4j_dir = os.path.join(script_dir, "neo4j_lpp")
    
    # Constants for weight calculation
    SERVICE_WINDOW = 18 * 3600  # 18 hours in seconds
    WALK_THRESHOLD = 300       # meters
    WALK_SPEED = 1.4           # meters per second
    
    # Ensure output directory exists
    os.makedirs(neo4j_dir, exist_ok=True)
    
    stops_csv = os.path.join(neo4j_dir, "neo4j_stops.csv")
    edges_csv = os.path.join(neo4j_dir, "neo4j_edges.csv")
    walk_edges_csv = os.path.join(neo4j_dir, "neo4j_walk_edges.csv")

    print("1. Parsing calendar dates for weekday service IDs...")
    weekday_services = set()
    with open(os.path.join(gtfs_dir, "calendar_dates.txt"), "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = datetime.strptime(row["date"], "%Y%m%d")
            # 0=Monday, 4=Friday
            if dt.weekday() < 5:
                weekday_services.add(row["service_id"])

    print(f"   Found {len(weekday_services)} weekday service IDs.")

    print("2. Identifying valid weekday trips...")
    valid_weekday_trips = set()
    with open(os.path.join(gtfs_dir, "trips.txt"), "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["service_id"] in weekday_services:
                valid_weekday_trips.add(row["trip_id"])
                
    print(f"   Found {len(valid_weekday_trips)} weekday trips.")

    print("3. Generating neo4j_stops.csv and caching coordinates...")
    stops_data = {}  # stop_id -> (lat, lon, name)
    stops_count = 0
    with open(os.path.join(gtfs_dir, "stops.txt"), "r", encoding="utf-8-sig") as f_in, \
         open(stops_csv, "w", newline="", encoding="utf-8") as f_out:
        
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=["stop_id", "name", "lat", "lon"])
        writer.writeheader()
        
        for row in reader:
            sid = row["stop_id"]
            name = row["stop_name"]
            lat = float(row["stop_lat"])
            lon = float(row["stop_lon"])
            
            stops_data[sid] = (lat, lon, name)
            writer.writerow({
                "stop_id": sid,
                "name": name,
                "lat": lat,
                "lon": lon
            })
            stops_count += 1
            
    print(f"   Exported {stops_count} stops.")

    print("4. Processing stop_times.txt to calculate travel durations...")
    # edge_stats[(src, tgt)] = [total_duration_seconds, trip_count]
    edge_stats = defaultdict(lambda: [0, 0])
    
    current_trip = None
    prev_stop = None
    prev_departure = None
    
    with open(os.path.join(gtfs_dir, "stop_times.txt"), "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i % 500000 == 0 and i > 0:
                print(f"   Processed {i} rows...")
                
            trip_id = row["trip_id"]
            if trip_id not in valid_weekday_trips:
                continue
                
            stop_id = row["stop_id"]
            arrival_time = time_to_seconds(row["arrival_time"])
            departure_time = time_to_seconds(row["departure_time"])
            
            if trip_id == current_trip:
                # Continuing current trip
                duration = arrival_time - prev_departure
                if duration >= 0:  # Data sanity check
                    edge_stats[(prev_stop, stop_id)][0] += duration
                    edge_stats[(prev_stop, stop_id)][1] += 1
            
            current_trip = trip_id
            prev_stop = stop_id
            prev_departure = departure_time

    print(f"   Found {len(edge_stats)} unique directed connections.")

    print("5. Generating neo4j_edges.csv (Bus weight = TravelTime + WaitPenalty)...")
    with open(edges_csv, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["source_stop_id", "target_stop_id", "weight", "type"])
        for (src, tgt), (total_dur, count) in edge_stats.items():
            avg_travel_time = total_dur / count
            # Wait penalty: Service window / (2 * count)
            wait_penalty = SERVICE_WINDOW / (2 * count)
            total_weight = avg_travel_time + wait_penalty
            
            writer.writerow([src, tgt, round(total_weight, 2), "BUS"])

    print("6. Generating neo4j_walk_edges.csv (Threshold: 300m)...")
    stop_ids = list(stops_data.keys())
    walk_count = 0
    with open(walk_edges_csv, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["source_stop_id", "target_stop_id", "weight", "type"])
        
        for i in range(len(stop_ids)):
            s1 = stop_ids[i]
            lat1, lon1, _ = stops_data[s1]
            
            for j in range(i + 1, len(stop_ids)):
                s2 = stop_ids[j]
                lat2, lon2, _ = stops_data[s2]
                
                # Fast distance pre-check (approx 0.003 degrees latitude is ~330m)
                if abs(lat1 - lat2) < 0.003 and abs(lon1 - lon2) < 0.005:
                    dist = haversine(lat1, lon1, lat2, lon2)
                    if dist <= WALK_THRESHOLD:
                        weight = dist / WALK_SPEED
                        # Walking is bidirectional
                        writer.writerow([s1, s2, round(weight, 2), "WALK"])
                        writer.writerow([s2, s1, round(weight, 2), "WALK"])
                        walk_count += 1
                        
    print(f"   Found {walk_count} walking connections.")
    print("Done! Data ready for Neo4j.")

if __name__ == "__main__":
    generate_neo4j_data()


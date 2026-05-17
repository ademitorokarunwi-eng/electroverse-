import json
import sqlite3
 
from flask import Flask, jsonify
 
app = Flask(__name__)
 
DATABASE_NAME = "database.db"
 
 
def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection
 
 
def create_tables():
    with get_connection() as connection:
        cursor = connection.cursor()
 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_reference TEXT UNIQUE,
                lat REAL,
                lon REAL,
                operator_reference TEXT,
                country_reference TEXT,
                postal_code TEXT,
                last_updated TEXT
            )
        """)
 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER,
                physical_identifier TEXT,
                status TEXT,
                FOREIGN KEY (location_id) REFERENCES locations (id)
            )
        """)
 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evse_id INTEGER,
                power INTEGER,
                standard TEXT,
                FOREIGN KEY (evse_id) REFERENCES evses (id)
            )
        """)
 
        connection.commit()
 
 
def import_integrated_data():
    with get_connection() as connection:
        cursor = connection.cursor()
 
        with open("integrated.json") as file:
            locations = json.load(file)
 
        print(f"Found {len(locations)} locations")
 
        for location in locations:
            coordinates = location["coordinates"]
 
            cursor.execute("""
                INSERT OR IGNORE INTO locations (
                    location_reference,
                    lat,
                    lon,
                    operator_reference,
                    country_reference,
                    postal_code,
                    last_updated
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                location["id"],
                float(coordinates["latitude"]),   # cast: stored as "50.801..." string in JSON
                float(coordinates["longitude"]),
                location["operator"]["name"] if location.get("operator") else None,  # was party_id
                location["country"],
                location["postal_code"],
                location["last_updated"],
            ))
 
            # If rowcount is 0, this location already existed — skip children
            # to avoid duplicating EVSEs and connectors on re-runs
            if cursor.rowcount == 0:
                continue
 
            location_row = cursor.execute(
                "SELECT id FROM locations WHERE location_reference = ?",
                (location["id"],)
            ).fetchone()
 
            location_id = location_row["id"]
 
            for evse in location["evses"]:
                cursor.execute("""
                    INSERT INTO evses (
                        location_id,
                        physical_identifier,
                        status
                    )
                    VALUES (?, ?, ?)
                """, (
                    location_id,
                    evse["physical_reference"],
                    evse["status"],
                ))
 
                evse_id = cursor.lastrowid
 
                for connector in evse["connectors"]:
                    cursor.execute("""
                        INSERT INTO connectors (
                            evse_id,
                            power,
                            standard
                        )
                        VALUES (?, ?, ?)
                    """, (
                        evse_id,
                        connector.get("max_electric_power"),
                        connector["standard"],
                    ))
 
        connection.commit()
 
 

@app.route("/locations")
def get_locations():
    with get_connection() as connection:
        cursor = connection.cursor()
        
        locations = cursor.execute("""
            SELECT * FROM locations
        """).fetchall()
        
        result = []
        for location in locations:
            evse_count = cursor.execute("""
                SELECT COUNT(*) FROM evses WHERE location_id = ?
            """, (location["id"],)).fetchone()[0]
            
            result.append({
                "coordinates": {
                    "lat": location["lat"],
                    "lon": location["lon"]
                },
                "operator_reference": location["operator_reference"],
                "country_reference": location["country_reference"],
                "postal_code": location["postal_code"],
                "number_of_evses": evse_count
            })
        
        return jsonify({"locations": result})
@app.route("/locations/<reference>")
def get_location(reference):
    with get_connection() as connection:
        cursor = connection.cursor()

        location = cursor.execute("""
            SELECT * FROM locations WHERE location_reference = ?
        """, (reference,)).fetchone()

        if not location:
            return jsonify({"error": "Location not found"}), 404

        evses = cursor.execute("""
            SELECT * FROM evses WHERE location_id = ?
        """, (location["id"],)).fetchall()

        evse_list = []
        for evse in evses:
            connectors = cursor.execute("""
                SELECT * FROM connectors WHERE evse_id = ?
            """, (evse["id"],)).fetchall()

            evse_list.append({
                "physical_identifier": evse["physical_identifier"],
                "status": evse["status"],
                "connectors": [{"power": c["power"], "standard": c["standard"]} for c in connectors]
            })

    result = {
    "coordinates": {
        "lat": location["lat"],
        "lon": location["lon"]
    },
    "operator_reference": location["operator_reference"],
    "country_reference": location["country_reference"],
    "postal_code": location["postal_code"],
    "evses": evse_list
}

    return jsonify(result)


if_name__ == "__main__":
    create_tables()
    import_integrated_data()
    app.run(debug=True)
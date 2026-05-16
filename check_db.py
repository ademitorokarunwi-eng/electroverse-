import sqlite3
 
with sqlite3.connect("database.db") as connection:
    cursor = connection.cursor()
 
    location_count = cursor.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
    evse_count = cursor.execute("SELECT COUNT(*) FROM evses").fetchone()[0]
    connector_count = cursor.execute("SELECT COUNT(*) FROM connectors").fetchone()[0]
 
    print("locations: ", location_count)
    print("evses:     ", evse_count)
    print("connectors:", connector_count)
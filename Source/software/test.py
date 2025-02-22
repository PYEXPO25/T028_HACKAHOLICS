def get_db_connection(database='smart_irrigation'):  # ✅ Use string for the default database
    try:
        config = DB_CONFIG.copy()
        config['database'] = database  # Set the database dynamically
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as e:
        print("Database connection failed:", e)
        return None
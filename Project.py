import psycopg2 as pg  # 'pscopg2' is used to interact with the PostgreSQL database

# Database Connection Parameters
DB_Name = "Project"
DB_USER = "User-Name"
DB_Password = "Password"
DB_HOST = "localhost"  # The database is hosted locally
DB_Port = "5432"  # Default port that is used for PostgreSQL

try: 
    conn = pg.connect(database=DB_Name, user=DB_USER, password=DB_Password, host=DB_HOST, port=DB_Port)
    cursor = conn.cursor()
    print("Connected to the database")
    
    cursor.close()
    conn.close()

except Exception as e:
    print("Error: ", e)
    print("Failed to connect to the database")
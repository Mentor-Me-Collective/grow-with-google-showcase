import sqlite3
import os

def init_db():
    schema_path = 'schema.sql'
    db_path = 'energy_optimizer.db'

    if not os.path.exists(schema_path):
        print(f"Error: {schema_path} not found in current directory.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(schema_path, 'r') as f:
        schema_script = f.read()

    cursor.executescript(schema_script)
    conn.commit()
    conn.close()

    print(f"Database '{db_path}' initialized successfully using '{schema_path}'.")

if __name__ == '__main__':
    init_db()
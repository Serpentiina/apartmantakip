from app import db, create_app
import sqlite3
import os

def migrate_database():
    app = create_app()
    
    with app.app_context():
        # Get the database path
        db_path = os.path.join(app.instance_path, 'apartman.db')
        print(f"Database path: {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add apartman_ismi column to user table
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN apartman_ismi TEXT DEFAULT 'Apartman'")
            print("Added apartman_ismi column to user table")
        except sqlite3.OperationalError as e:
            print(f"Error adding apartman_ismi to user: {e}")
        
        # Add user_id column to daire table
        try:
            cursor.execute("ALTER TABLE daire ADD COLUMN user_id INTEGER REFERENCES user(id)")
            print("Added user_id column to daire table")
        except sqlite3.OperationalError as e:
            print(f"Error adding user_id to daire: {e}")
        
        # Add user_id column to aidat table
        try:
            cursor.execute("ALTER TABLE aidat ADD COLUMN user_id INTEGER REFERENCES user(id)")
            print("Added user_id column to aidat table")
        except sqlite3.OperationalError as e:
            print(f"Error adding user_id to aidat: {e}")
        
        # Add user_id column to gider table
        try:
            cursor.execute("ALTER TABLE gider ADD COLUMN user_id INTEGER REFERENCES user(id)")
            print("Added user_id column to gider table")
        except sqlite3.OperationalError as e:
            print(f"Error adding user_id to gider: {e}")
        
        # Add user_id column to duyuru table
        try:
            cursor.execute("ALTER TABLE duyuru ADD COLUMN user_id INTEGER REFERENCES user(id)")
            print("Added user_id column to duyuru table")
        except sqlite3.OperationalError as e:
            print(f"Error adding user_id to duyuru: {e}")
        
        # Set default user_id for existing records
        # Get the first admin user
        cursor.execute("SELECT id FROM user WHERE is_admin = 1 LIMIT 1")
        admin_id = cursor.fetchone()
        
        if admin_id:
            admin_id = admin_id[0]
            print(f"Setting default user_id to {admin_id} for all existing records")
            
            # Update daire records
            cursor.execute(f"UPDATE daire SET user_id = {admin_id} WHERE user_id IS NULL")
            print(f"Updated {cursor.rowcount} daire records")
            
            # Update aidat records
            cursor.execute(f"UPDATE aidat SET user_id = {admin_id} WHERE user_id IS NULL")
            print(f"Updated {cursor.rowcount} aidat records")
            
            # Update gider records
            cursor.execute(f"UPDATE gider SET user_id = {admin_id} WHERE user_id IS NULL")
            print(f"Updated {cursor.rowcount} gider records")
            
            # Update duyuru records
            cursor.execute(f"UPDATE duyuru SET user_id = {admin_id} WHERE user_id IS NULL")
            print(f"Updated {cursor.rowcount} duyuru records")
        else:
            print("No admin user found. Please create an admin user first.")
        
        # Commit the changes
        conn.commit()
        conn.close()
        
        print("Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database() 
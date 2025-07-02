import os
import pymysql
from dotenv import load_dotenv
import uuid

load_dotenv()

def update_schema():
    try:
        # MySQL connection parameters
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'db': os.getenv('DB_NAME', 'farmers_chatbot'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        
        print("Connecting to MySQL...")
        conn = pymysql.connect(**db_config)
        
        with conn.cursor() as cursor:
            # Drop existing tables if they exist to recreate with proper schema
            print("Dropping existing tables...")
            cursor.execute("DROP TABLE IF EXISTS soil_reports")
            cursor.execute("DROP TABLE IF EXISTS plant_images")
            cursor.execute("DROP TABLE IF EXISTS chat_history")
            cursor.execute("DROP TABLE IF EXISTS messages")
            cursor.execute("DROP TABLE IF EXISTS chat_sessions")
            
            # Create tables with updated schema
            print("Creating chat_sessions table...")
            cursor.execute("""
            CREATE TABLE chat_sessions (
                id VARCHAR(36) PRIMARY KEY,
                user_id INT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                language VARCHAR(20) DEFAULT 'hindi',
                INDEX idx_user_id (user_id)
            )
            """)
            
            print("Creating messages table...")
            cursor.execute("""
            CREATE TABLE messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id VARCHAR(36) NOT NULL,
                user_id INT NULL,
                text TEXT NOT NULL,
                sender VARCHAR(10) NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                input_type VARCHAR(20) DEFAULT 'text',
                FOREIGN KEY (chat_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_chat_timestamp (chat_id, timestamp)
            )
            """)
            
            print("Creating plant_images table...")
            cursor.execute("""
            CREATE TABLE plant_images (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NULL,
                chat_id VARCHAR(36) NOT NULL,
                message_id INT NULL,
                image_path VARCHAR(255) NOT NULL,
                plant_type VARCHAR(100) NULL,
                disease VARCHAR(100) NULL,
                confidence FLOAT NULL,
                recommendation TEXT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL,
                INDEX idx_user_id (user_id)
            )
            """)
            
            print("Creating soil_reports table...")
            cursor.execute("""
            CREATE TABLE soil_reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NULL,
                chat_id VARCHAR(36) NOT NULL,
                message_id INT NULL,
                report_path VARCHAR(255) NOT NULL,
                soil_type VARCHAR(100) NULL,
                ph FLOAT NULL,
                nitrogen FLOAT NULL,
                phosphorus FLOAT NULL,
                potassium FLOAT NULL,
                crop_recommendations TEXT NULL,
                fertilizer_recommendations TEXT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL,
                INDEX idx_user_id (user_id)
            )
            """)
            
            # Create a test chat session (not associated with a user)
            test_chat_id = str(uuid.uuid4())
            print(f"Creating test chat session with ID: {test_chat_id}")
            cursor.execute(
                "INSERT INTO chat_sessions (id, language, user_id) VALUES (%s, %s, NULL)",
                (test_chat_id, 'hindi')
            )
            
            # Add a welcome message
            welcome_msg = "नमस्ते! मैं आपका AI ग्रीन साथी हूँ। आज मैं आपकी खेती संबंधित प्रश्नों में कैसे मदद कर सकता हूँ?"
            cursor.execute(
                "INSERT INTO messages (chat_id, text, sender, user_id) VALUES (%s, %s, %s, NULL)",
                (test_chat_id, welcome_msg, 'bot')
            )
            
            conn.commit()
            
            print("\nSchema updated successfully!")
            print(f"You can now test the app with chat_id: {test_chat_id}")
            
    except Exception as e:
        print(f"\nError updating schema: {str(e)}")
        return False

def migrate_data():
    """Migrate data from old tables to new schema if they exist"""
    try:
        # MySQL connection parameters
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'db': os.getenv('DB_NAME', 'farmers_chatbot'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        
        print("Connecting to MySQL for data migration...")
        conn = pymysql.connect(**db_config)
        
        with conn.cursor() as cursor:
            # Check if the old chat_history table exists
            cursor.execute("SHOW TABLES LIKE 'chat_history'")
            if cursor.fetchone():
                print("Migrating data from chat_history table...")
                
                # First, get all unique chat_ids from chat_history
                cursor.execute("SELECT DISTINCT chat_id FROM chat_history WHERE chat_id IS NOT NULL")
                chat_ids = cursor.fetchall()
                
                for chat in chat_ids:
                    chat_id = chat['chat_id']
                    
                    # Create chat session if it doesn't exist
                    cursor.execute("SELECT id FROM chat_sessions WHERE id = %s", (chat_id,))
                    if not cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO chat_sessions (id, language, user_id) VALUES (%s, %s, NULL)",
                            (chat_id, 'hindi')
                        )
                
                # Migrate user messages and bot responses
                cursor.execute("""
                    SELECT * FROM chat_history WHERE chat_id IS NOT NULL ORDER BY created_at
                """)
                history_rows = cursor.fetchall()
                
                for row in history_rows:
                    # Insert user message
                    cursor.execute(
                        "INSERT INTO messages (chat_id, user_id, text, sender, input_type) VALUES (%s, %s, %s, %s, %s)",
                        (row['chat_id'], row['user_id'], row['user_message'], 'user', row['input_type'])
                    )
                    
                    # Insert bot response
                    cursor.execute(
                        "INSERT INTO messages (chat_id, user_id, text, sender) VALUES (%s, %s, %s, %s)",
                        (row['chat_id'], None, row['bot_response'], 'bot')
                    )
            
            # Migrate plant diagnoses if they exist
            cursor.execute("SHOW TABLES LIKE 'plant_diagnoses'")
            if cursor.fetchone():
                print("Migrating data from plant_diagnoses table...")
                
                # For each diagnosis, create a chat session if needed and add messages
                cursor.execute("SELECT * FROM plant_diagnoses")
                diagnoses = cursor.fetchall()
                
                for diagnosis in diagnoses:
                    # Create a new chat session for each plant diagnosis
                    new_chat_id = str(uuid.uuid4())
                    cursor.execute(
                        "INSERT INTO chat_sessions (id, user_id, language) VALUES (%s, %s, %s)",
                        (new_chat_id, diagnosis['user_id'], 'english')
                    )
                    
                    # Add user message
                    cursor.execute(
                        "INSERT INTO messages (chat_id, user_id, text, sender, input_type) VALUES (%s, %s, %s, %s, %s)",
                        (new_chat_id, diagnosis['user_id'], "Plant image uploaded for diagnosis", 'user', 'image')
                    )
                    message_id = cursor.lastrowid
                    
                    # Add plant image record
                    cursor.execute(
                        """INSERT INTO plant_images 
                           (user_id, chat_id, message_id, image_path, plant_type, disease, confidence, recommendation) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (diagnosis['user_id'], new_chat_id, message_id, diagnosis['image_path'], 
                         diagnosis['plant_type'], diagnosis['disease_name'], 
                         diagnosis['confidence_score'], diagnosis['recommendation'])
                    )
                    
                    # Add bot response
                    response_text = f"Plant type: {diagnosis['plant_type']}\nDisease: {diagnosis['disease_name']}\nConfidence: {diagnosis['confidence_score']}\nRecommendation: {diagnosis['recommendation']}"
                    cursor.execute(
                        "INSERT INTO messages (chat_id, user_id, text, sender) VALUES (%s, %s, %s, %s)",
                        (new_chat_id, None, response_text, 'bot')
                    )
            
            conn.commit()
            print("Data migration completed successfully!")
            
    except Exception as e:
        print(f"Error migrating data: {str(e)}")
        return False

if __name__ == "__main__":
    update_schema()
    migrate_data() 
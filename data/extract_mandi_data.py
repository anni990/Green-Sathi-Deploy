import os
import requests
import json
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mandi_data_extraction.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create and return a database connection"""
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'farmers_chatbot')
    )

def parse_date(date_str):
    """Parse date from DD/MM/YYYY format to YYYY-MM-DD"""
    try:
        day, month, year = date_str.split('/')
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except Exception as e:
        logging.warning(f"Invalid date format: {date_str} | Error: {str(e)}")
        return None

def fetch_mandi_data():
    """Fetch complete mandi data from the API using pagination with delay"""
    try:
        api_key = os.getenv('MANDI_API_KEY')
        if not api_key:
            raise ValueError("MANDI_API_KEY not found in environment variables")

        base_url = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
        limit = 5000
        offset = 0
        all_records = []

        # Get today's date in YYYY-MM-DD format
        today_date = "2025-05-23"

        while True:
            url = f"{base_url}?api-key={api_key}&format=json&limit={limit}&offset={offset}&filters%5BArrival_Date%5D={today_date}"
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()
            records = data.get('records', [])

            if not records:
                break  # No more data to fetch

            # Process each record to match database schema
            processed_records = []
            for record in records:
                processed_record = {
                    'state': record.get('State', '').strip(),
                    'district': record.get('District', '').strip(),
                    'market': record.get('Market', '').strip(),
                    'commodity': record.get('Commodity', '').strip(),
                    'variety': record.get('Variety', '').strip(),
                    'grade': record.get('Grade', '').strip(),
                    'arrival_date': parse_date(record.get('Arrival_Date', '')),
                    'min_price': float(record.get('Min_Price', 0)),
                    'max_price': float(record.get('Max_Price', 0)),
                    'modal_price': float(record.get('Modal_Price', 0))
                }
                processed_records.append(processed_record)

            all_records.extend(processed_records)
            logging.info(f"Fetched and processed {len(processed_records)} records at offset {offset}")

            offset += limit  # Move to next page
            time.sleep(1)  # Add 1-second delay between requests

        return all_records

    except Exception as e:
        logging.error(f"Error fetching mandi data: {str(e)}")
        raise

def process_and_store_data(records):
    """Process and store the mandi data in the database"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Prepare insert query matching table schema
        insert_query = """
        INSERT INTO mandi_data 
        (state, district, market, commodity, variety, grade, arrival_date, min_price, max_price, modal_price)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        inserted_count = 0
        for record in records:
            try:
                # Skip records with invalid dates
                if not record['arrival_date']:
                    logging.warning(f"Skipping record due to invalid date: {record}")
                    continue

                # Insert record
                cursor.execute(insert_query, (
                    record['state'],
                    record['district'],
                    record['market'],
                    record['commodity'],
                    record['variety'],
                    record['grade'],
                    record['arrival_date'],
                    record['min_price'],
                    record['max_price'],
                    record['modal_price']
                ))
                inserted_count += 1

            except Exception as e:
                logging.error(f"Error processing record: {str(e)} | Record: {record}")
                continue

        conn.commit()
        logging.info(f"Successfully inserted {inserted_count} new records.")

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Database error: {str(e)}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def main():
    """Main function to orchestrate the data extraction and storage process"""
    try:
        logging.info("Starting mandi data extraction process")
        
        # Fetch data from API
        records = fetch_mandi_data()
        logging.info(f"Fetched {len(records)} records from API")
        
        # Process and store data
        process_and_store_data(records)
        
        logging.info("Mandi data extraction completed successfully")
        
    except Exception as e:
        logging.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
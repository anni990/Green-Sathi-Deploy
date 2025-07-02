import numpy as np
from sklearn.neighbors import BallTree
import mysql.connector
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_db_connection():
    """Create database connection"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'farmers_chatbot')
        )
        logger.info("Database connection successful")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

def ensure_districts_coordinates_table():
    """Ensure the districts_coordinates table exists and has data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'districts_coordinates'")
        if not cursor.fetchone():
            logger.info("Creating districts_coordinates table")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS districts_coordinates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    district_name VARCHAR(255) NOT NULL,
                    state_name VARCHAR(255) NOT NULL,
                    latitude DECIMAL(10, 8) NOT NULL,
                    longitude DECIMAL(11, 8) NOT NULL,
                    UNIQUE KEY unique_district (district_name, state_name)
                )
            """)
            conn.commit()
            logger.info("districts_coordinates table created")
        
        # Check if table has data
        cursor.execute("SELECT COUNT(*) FROM districts_coordinates")
        count = cursor.fetchone()[0]
        if count == 0:
            logger.warning("districts_coordinates table is empty")
            # You might want to add some sample data here
            cursor.execute("""
                INSERT INTO districts_coordinates (district_name, state_name, latitude, longitude)
                VALUES 
                ('Delhi', 'Delhi', 28.6139, 77.2090),
                ('Mumbai', 'Maharashtra', 19.0760, 72.8777),
                ('Bangalore', 'Karnataka', 12.9716, 77.5946)
            """)
            conn.commit()
            logger.info("Added sample data to districts_coordinates table")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error ensuring districts_coordinates table: {str(e)}")
        return False

def get_nearest_districts(latitude, longitude, k=5):
    """
    Get the k nearest districts to the given latitude and longitude.
    Returns a list of dictionaries with district_name, state_name, and distance.
    """
    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch all district coordinates
        cursor.execute("SELECT district_name, state_name, latitude, longitude FROM districts_coordinates")
        districts = cursor.fetchall()

        if not districts:
            logger.warning("No district data found.")
            return []

        # Prepare coordinates in radians
        coords = np.radians(np.array([[d['latitude'], d['longitude']] for d in districts]))

        # Create BallTree
        tree = BallTree(coords, metric='haversine')

        # User coordinates to radians
        user_coords = np.radians([[latitude, longitude]])

        # Query nearest
        k = min(k, len(districts))  # avoid asking more neighbors than available
        distances, indices = tree.query(user_coords, k=k)

        # Convert distances to KM
        distances_km = distances[0] * 6371  # Earth's radius

        # Build result
        result = []
        for i, idx in enumerate(indices[0]):
            d = districts[idx]
            result.append({
                'district_name': d['district_name'],
                'state_name': d['state_name'],
                'distance': round(distances_km[i], 2)
            })

        return result

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

def get_mandi_data_for_districts(district_names, commodity=None, market=None):
    """
    Get mandi data for specified districts with optional commodity and market filters.
    Returns data in a format suitable for charts and tables.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Extract district and state names
        district_list = []
        state_list = []
        if isinstance(district_names, list):
            for item in district_names:
                if isinstance(item, dict):
                    district_list.append(item['district_name'])
                    state_list.append(item['state_name'])
                else:
                    district_list.append(item)
        
        # Get latest date for these districts
        latest_date_query = """
            SELECT MAX(arrival_date) as latest_date
            FROM mandi_data
            WHERE district IN ({})
        """.format(','.join(['%s'] * len(district_list)))
        
        cursor.execute(latest_date_query, tuple(district_list))
        latest_date_result = cursor.fetchone()
        
        if not latest_date_result or not latest_date_result['latest_date']:
            logger.warning(f"No data found for districts: {district_list}")
            return {
                'table_data': [],
                'commodity_distribution': {'labels': [], 'data': []},
                'market_comparison': {'labels': [], 'data': []},
                'price_ranges': {'labels': [], 'data': []}
            }
            
        latest_date = latest_date_result['latest_date']
        
        # Get data for the latest date
        query = """
            SELECT 
                state, district, market, commodity, variety, grade,
                arrival_date, min_price, max_price, modal_price
            FROM mandi_data
            WHERE district IN ({})
            AND arrival_date = %s
        """.format(','.join(['%s'] * len(district_list)))
        
        params = district_list + [latest_date]
        
        # Add state filter if available
        if state_list:
            query = """
                SELECT 
                    state, district, market, commodity, variety, grade,
                    arrival_date, min_price, max_price, modal_price
                FROM mandi_data
                WHERE state IN ({})
                AND district IN ({})
                AND arrival_date = %s
            """.format(
                ','.join(['%s'] * len(state_list)),
                ','.join(['%s'] * len(district_list))
            )
            params = state_list + district_list + [latest_date]
        
        # Add optional filters
        if commodity:
            query += " AND commodity = %s"
            params.append(commodity)
        if market:
            query += " AND market = %s"
            params.append(market)
            
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        if not results:
            logger.warning(f"No mandi data found for the specified filters")
            return {
                'table_data': [],
                'commodity_distribution': {'labels': [], 'data': []},
                'market_comparison': {'labels': [], 'data': []},
                'price_ranges': {'labels': [], 'data': []}
            }
            
        logger.info(f"Found {len(results)} records for the specified filters")
        
        # Initialize processed data structure
        processed_data = {
            'table_data': [],
            'commodity_distribution': {'labels': [], 'data': []},
            'market_comparison': {'labels': [], 'data': []},
            'price_ranges': {'labels': [], 'data': []}
        }
        
        # Process each record
        for record in results:
            # Add to table data
            processed_data['table_data'].append({
                'state': record['state'],
                'district': record['district'],
                'market': record['market'],
                'commodity': record['commodity'],
                'variety': record['variety'] or '-',
                'grade': record['grade'] or '-',
                'arrival_date': record['arrival_date'].strftime('%Y-%m-%d'),
                'min_price': float(record['min_price']),
                'max_price': float(record['max_price']),
                'modal_price': float(record['modal_price'])
            })
            
            # Update commodity distribution
            commodity = record['commodity']
            if commodity not in processed_data['commodity_distribution']['labels']:
                processed_data['commodity_distribution']['labels'].append(commodity)
                processed_data['commodity_distribution']['data'].append(1)
            else:
                idx = processed_data['commodity_distribution']['labels'].index(commodity)
                processed_data['commodity_distribution']['data'][idx] += 1
            
            # Update market comparison
            market = record['market']
            if market not in processed_data['market_comparison']['labels']:
                processed_data['market_comparison']['labels'].append(market)
                processed_data['market_comparison']['data'].append(float(record['modal_price']))
            else:
                idx = processed_data['market_comparison']['labels'].index(market)
                processed_data['market_comparison']['data'][idx] = (processed_data['market_comparison']['data'][idx] + float(record['modal_price'])) / 2
            
            # Update price ranges
            commodity = record['commodity']
            if commodity not in processed_data['price_ranges']['labels']:
                processed_data['price_ranges']['labels'].append(commodity)
                processed_data['price_ranges']['data'].append({
                    'min': float(record['min_price']),
                    'max': float(record['max_price']),
                    'avg': float(record['modal_price'])
                })
            else:
                idx = processed_data['price_ranges']['labels'].index(commodity)
                current = processed_data['price_ranges']['data'][idx]
                current['min'] = min(current['min'], float(record['min_price']))
                current['max'] = max(current['max'], float(record['max_price']))
                current['avg'] = (current['avg'] + float(record['modal_price'])) / 2
        
        return processed_data
        
    except Exception as e:
        logger.error(f"Error in get_mandi_data_for_districts: {str(e)}")
        return {
            'table_data': [],
            'commodity_distribution': {'labels': [], 'data': []},
            'market_comparison': {'labels': [], 'data': []},
            'price_ranges': {'labels': [], 'data': []}
        }
    finally:
        if conn:
            conn.close() 
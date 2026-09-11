import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env')

try:
    psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        dbname=os.getenv('DB_NAME')
    )
except Exception as e:
    # Get the raw bytes of the exception message if possible
    try:
        raw_msg = str(e).encode('utf-8', 'ignore')
        print("Raw error:", raw_msg)
    except:
        pass
    print("Type of error:", type(e))

import sys
sys.path.append("site-packages")

import psycopg2
conn = psycopg2.connect(
        host="localhost",
        dbname="taras_trader",
        user="postgres",
        password="pcl340"
    )

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect("dbname=taras_trader user=postgres password=pcl340")
		
        # create a cursor
        cur = conn.cursor()
        
	# execute a statement
        cur.execute("""
            CREATE TABLE stocks (
                symbol VARCHAR(10) PRIMARY KEY,
                max_price NUMERIC(7,2),
                second_max_price NUMERIC(7,2),
                drop_price NUMERIC(7,2)
            )
        """)
       
	# close the communication with the PostgreSQL
        cur.close()
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')


if __name__ == '__main__':
    connect()
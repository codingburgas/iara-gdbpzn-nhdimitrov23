import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def get_connection(self):
        """Get database connection, creating one if needed"""
        try:
            if self._connection is None or self._connection.closed:
                self._connection = psycopg2.connect(
                    host=os.getenv('POSTGRES_HOST', 'localhost'),
                    database=os.getenv('POSTGRES_DB'),
                    user=os.getenv('POSTGRES_USER'),
                    password=os.getenv('POSTGRES_PASSWORD'),
                    port=os.getenv('POSTGRES_PORT', '5432')
                )
                self._connection.autocommit = False
            return self._connection
        except Exception as e:
            print(f"Database connection error: {e}")
            raise

    def get_cursor(self, dict_cursor=True):
        """Get a database cursor"""
        conn = self.get_connection()
        if dict_cursor:
            return conn.cursor(cursor_factory=RealDictCursor)
        return conn.cursor()

    def commit(self):
        """Commit the current transaction"""
        if self._connection and not self._connection.closed:
            self._connection.commit()

    def rollback(self):
        """Rollback the current transaction"""
        if self._connection and not self._connection.closed:
            self._connection.rollback()

    def close(self):
        """Close the database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None


db = Database()
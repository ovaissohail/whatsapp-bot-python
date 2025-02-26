from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv
import os
import certifi

load_dotenv()

class MongoDBConnection:
    _instance: Optional['MongoDBConnection'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._client:
            try:
                mongodb_uri = os.getenv('MONGODB_URI')
                db_name = os.getenv('MONGODB_DB_NAME')
                
                if not mongodb_uri or not db_name:
                    raise ValueError("MongoDB URI or DB_NAME not found in environment variables")
                
                print(f"Connecting to database: {db_name}")  # Debug log
                
                # If using MongoDB Atlas (URI starts with mongodb+srv://)
                if mongodb_uri.startswith('mongodb+srv://'):
                    self._client = MongoClient(
                        mongodb_uri,
                        serverSelectionTimeoutMS=5000,  # 5 second timeout
                        tlsCAFile=certifi.where(),
                        retryWrites=True,
                        w='majority'
                    )
                else:
                    self._client = MongoClient(mongodb_uri)
                
                # Test the connection
                self._client.server_info()  # This will raise an exception if connection fails
                print("Successfully connected to MongoDB")  # Debug log
                
                self._db = self._client[db_name]
                
            except Exception as e:
                print(f"Failed to connect to MongoDB: {str(e)}")  # Debug log
                raise

    @property
    def db(self) -> Database:
        return self._db

    def close(self):
        if self._client:
            self._client.close()

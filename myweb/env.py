import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DEBUG = os.getenv("DEBUG") == "True"
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY") 
JWT_ACCESS_TOKEN_EXPIRATION = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRATION"))  
JWT_REFRESH_TOKEN_EXPIRATION = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRATION")) 
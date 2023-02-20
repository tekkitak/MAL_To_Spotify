from os import system, getenv
from dotenv import load_dotenv 

load_dotenv()
system(f'flask run --host={getenv("FLASK_HOST", "127.0.0.1")} --port={getenv("FLASK_PORT", "5000")}')
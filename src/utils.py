import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
log_file_path=os.getenv("log_file_path")

def logger(message):
    try:
        with open(log_file_path, "a") as log_file:
            log_file.write(f"{datetime.now()} - {message}\n")
            print(f"{datetime.now()} - {message}")
    except Exception as e:
        print(f"\n{datetime.now()} - Error writing to log file.\n")
import os
import sys

# Ensure root project directory is on sys.path for Vercel serverless imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.main import app

# Vercel serverless entrypoint
handler = app
app = app

import subprocess
import sys

def app(environ, start_response):
    """WSGI application wrapper for Streamlit"""
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b"Streamlit app running"]

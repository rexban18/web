import os
import subprocess
import sqlite3
import threading
import signal
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_PATH = os.path.join(os.getcwd(), 'database', 'scripts.db')
LOG_PATH = os.path.join(os.getcwd(), 'script_output.log')
RUNNING_PROCESS = None
TIMER_THREAD = None

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def run_script(script_path, duration_seconds):
    global RUNNING_PROCESS
    
    # Update DB status
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE scripts SET status = 'running'")
    conn.commit()
    conn.close()

    try:
        # Clear previous log
        with open(LOG_PATH, 'w') as f:
            f.write(f"Starting script: {script_path}\n")
        
        # Start process
        with open(LOG_PATH, 'a') as log_file:
            RUNNING_PROCESS = subprocess.Popen(
                [sys.executable, script_path],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True
            )
            
        # Wait for process to finish or timeout
        try:
            RUNNING_PROCESS.wait(timeout=duration_seconds)
        except subprocess.TimeoutExpired:
            RUNNING_PROCESS.kill()
            with open(LOG_PATH, 'a') as f:
                f.write("\n[SYSTEM] Script stopped automatically after time limit.\n")

    except Exception as e:
        with open(LOG_PATH, 'a') as f:
            f.write(f"\n[ERROR] {str(e)}\n")
    finally:
        # Update DB to stopped
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE scripts SET status = 'stopped'")
        conn.commit()
        conn.close()
        RUNNING_PROCESS = None

@app.route('/api/start', methods=['POST'])
def start_script():
    global RUNNING_PROCESS, TIMER_THREAD
    
    if RUNNING_PROCESS and RUNNING_PROCESS.poll() is None:
        return jsonify({"error": "A script is already running"}), 400

    data = request.json
    script_id = data.get('id')
    duration = data.get('duration') # in hours

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM scripts WHERE id = ?", (script_id,))
    script = c.fetchone()
    conn.close()

    if not script:
        return jsonify({"error": "Script not found"}), 404

    duration_seconds = int(duration) * 3600
    
    # Run in a thread so the API response returns immediately
    # NOTE: In Vercel Serverless, this thread dies when the request times out (max 60s).
    # This works for demos but not for long-running production jobs on Vercel.
    thread = threading.Thread(target=run_script, args=(script['script_path'], duration_seconds))
    thread.start()

    return jsonify({"message": "Script started", "duration_hours": duration})

@app.route('/api/start', methods=['OPTIONS'])
def options():
    return '', 200

if __name__ == '__main__':
    app.run()
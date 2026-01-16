import os
import sqlite3
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Ensure directories exist
os.makedirs(os.path.join(os.getcwd(), 'scripts'), exist_ok=True)
os.makedirs(os.path.join(os.getcwd(), 'database'), exist_ok=True)

DB_PATH = os.path.join(os.getcwd(), 'database', 'scripts.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scripts (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 script_name TEXT,
                 script_path TEXT,
                 run_time TEXT,
                 status TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.py'):
        filename = secure_filename(file.filename)
        save_path = os.path.join(os.getcwd(), 'scripts', filename)
        file.save(save_path)
        
        init_db()
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO scripts (script_name, script_path, status) VALUES (?, ?, ?)",
                  (filename, save_path, 'uploaded'))
        conn.commit()
        script_id = c.lastrowid
        conn.close()
        
        return jsonify({"message": "File uploaded successfully", "id": script_id, "filename": filename})
    
    return jsonify({"error": "Invalid file type. Only .py allowed"}), 400

@app.route('/api/upload', methods=['OPTIONS'])
def options():
    return '', 200

if __name__ == '__main__':
    app.run()
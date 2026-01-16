import os
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)
LOG_PATH = os.path.join(os.getcwd(), 'script_output.log')

@app.route('/api/logs', methods=['GET'])
def get_logs():
    if not os.path.exists(LOG_PATH):
        return jsonify({"logs": "Waiting for script to run..."})
    
    with open(LOG_PATH, 'r') as f:
        content = f.read()
    
    return jsonify({"logs": content})

@app.route('/api/logs', methods=['OPTIONS'])
def options():
    return '', 200

if __name__ == '__main__':
    app.run()
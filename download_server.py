
from flask import Flask, send_from_directory, jsonify, render_template_string
import os

app = Flask(__name__)

# HTML template for the download page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kerala Lottery Results - Download</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .file-list { margin-top: 20px; }
        .file-item { 
            padding: 10px; 
            margin: 5px 0; 
            background: #f5f5f5; 
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .download-btn { 
            background: #007bff; 
            color: white; 
            padding: 5px 15px; 
            text-decoration: none; 
            border-radius: 3px;
        }
        .download-btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <h1>Kerala Lottery Results - JSON Downloads</h1>
    <p>Click on any file to download the lottery results in JSON format.</p>
    
    <div class="file-list">
        {% for file in files %}
        <div class="file-item">
            <span>{{ file }}</span>
            <a href="/download/{{ file }}" class="download-btn">Download</a>
        </div>
        {% endfor %}
    </div>
    
    {% if not files %}
    <p>No result files available yet.</p>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    # Get all JSON files from the note directory
    note_dir = 'note'
    files = []
    if os.path.exists(note_dir):
        files = [f for f in os.listdir(note_dir) if f.endswith('.json')]
        files.sort(reverse=True)  # Show newest first
    
    return render_template_string(HTML_TEMPLATE, files=files)

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory('note', filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/files')
def list_files():
    # API endpoint to get list of files
    note_dir = 'note'
    files = []
    if os.path.exists(note_dir):
        files = [f for f in os.listdir(note_dir) if f.endswith('.json')]
        files.sort(reverse=True)
    
    return jsonify({'files': files})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

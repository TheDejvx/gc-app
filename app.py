from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import os
from pymongo import MongoClient

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), 'gc_data.json')

_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
    uri = os.environ.get('MONGODB_URI')
    if not uri:
        return None
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        _db = client.get_default_database()
        print('Connected to MongoDB')
    except Exception as e:
        print(f'MongoDB connection failed: {e}')
    return _db


def load_data():
    db = get_db()
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        file_data = json.load(f)
    if db is not None:
        doc = db.gc_state.find_one({'_id': 'current'})
        if doc:
            doc.pop('_id')
            new_keys = [k for k in file_data if k not in doc]
            if new_keys:
                for k in new_keys:
                    doc[k] = file_data[k]
                save_data(doc)
                print(f'Migrated new keys to MongoDB: {new_keys}')
            return doc
        _seed_db(db, file_data)
    return file_data


def save_data(data):
    db = get_db()
    if db is not None:
        db.gc_state.replace_one({'_id': 'current'}, {'_id': 'current', **data}, upsert=True)
        return
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _seed_db(db, data):
    if db.gc_state.count_documents({'_id': 'current'}) == 0:
        db.gc_state.insert_one({'_id': 'current', **data})
        print('Seeded MongoDB from gc_data.json')


@app.route('/api/health')
def health():
    db = get_db()
    return jsonify({'db': 'mongodb' if db is not None else 'file'})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')


@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')


@app.route('/api/data')
def get_data():
    return jsonify(load_data())


@app.route('/api/save', methods=['POST'])
def save():
    try:
        data = request.json
        save_data(data)
        return jsonify({'status': 'ok', 'message': 'Sparat!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f'GC-appen körs på http://localhost:{port}')
    app.run(debug=True, port=port)

from flask import Flask, render_template, jsonify, request
import json
import os
import time
import threading
import requests as http
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


@app.route('/')
def index():
    return render_template('index.html')


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



# ── Systembolaget product search ──────────────────────────────────────────────
_SB_URL   = 'https://raw.githubusercontent.com/AlexGustafsson/systembolaget-api-data/main/data/assortment.json'
_SB_CACHE = os.path.join(os.path.dirname(__file__), 'sb_cache.json')
_SB_TTL   = 24 * 60 * 60  # 24 h

_sb_products = None
_sb_loading  = False
_sb_lock     = threading.Lock()

def _sb_load():
    global _sb_products, _sb_loading
    with _sb_lock:
        if _sb_loading:
            return
        _sb_loading = True
    try:
        if os.path.exists(_SB_CACHE) and (time.time() - os.path.getmtime(_SB_CACHE)) < _SB_TTL:
            with open(_SB_CACHE, 'r', encoding='utf-8') as f:
                _sb_products = json.load(f)
            print(f'SB: loaded {len(_sb_products)} products from cache')
            return
        print('SB: downloading assortment...')
        r = http.get(_SB_URL, timeout=60)
        r.raise_for_status()
        raw = r.json()
        products = []
        for p in raw:
            bold = p.get('productNameBold') or p.get('ProductNameBold') or ''
            thin = p.get('productNameThin') or p.get('ProductNameThin') or ''
            name = f'{bold} {thin}'.strip() or p.get('name') or p.get('Name') or ''
            if not name:
                continue
            price = p.get('price') or p.get('Price') or p.get('PriceInclVAT')
            products.append({
                'name':  name,
                'price': round(float(price), 2) if price else None,
                'cat':   str(p.get('categoryLevel1') or p.get('Category') or ''),
                'vol':   str(p.get('volumeText')     or p.get('Volume')   or ''),
            })
        _sb_products = products
        with open(_SB_CACHE, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False)
        print(f'SB: cached {len(products)} products')
    except Exception as e:
        print(f'SB: load failed – {e}')
    finally:
        _sb_loading = False

@app.route('/api/sb_search')
def sb_search():
    q = request.args.get('q', '').strip().lower()
    if len(q) < 2:
        return jsonify([])
    if _sb_products is None:
        threading.Thread(target=_sb_load, daemon=True).start()
        return jsonify([])
    results = [p for p in _sb_products if q in p['name'].lower()][:15]
    return jsonify(results)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f'GC-appen körs på http://localhost:{port}')
    app.run(debug=True, port=port)

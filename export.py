import json
import os
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore

# =========================
# 🔹 CONFIG
# =========================

VERSION_FILE = "version.json"
PELIS_FILE = "peliculas_index.json"
SERIES_FILE = "series_index.json"

# =========================
# 🔹 FIREBASE INIT
# =========================

cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# =========================
# 🔹 FUNCIONES AUX
# =========================

def file_hash(data: dict) -> str:
    """Genera un hash estable del contenido"""
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.md5(encoded).hexdigest()

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# 🔹 LEER VERSION ACTUAL
# =========================

current_version = 0
if os.path.exists(VERSION_FILE):
    with open(VERSION_FILE, "r") as f:
        current_version = json.load(f).get("version", 0)

# =========================
# 🔹 EXPORTAR PELÍCULAS
# =========================

peliculas_items = []

for doc in db.collection("peliculas").stream():
    data = doc.to_dict()

    if data.get("estado") != "activo":
        continue

    fuentes = data.get("fuentes", {})
    if not fuentes:
        continue

    peliculas_items.append({
        "_created": doc.create_time.timestamp(),  # 🔹 SOLO para ordenar
        "id": f"p_{data.get('tmdb_id')}",
        "tmdb_id": data.get("tmdb_id"),
        "nombre": data.get("nombre"),
        "poster": data.get("portada"),
        "calidad": data.get("calidad"),
        "generos": data.get("generos", []),
        "fuentes": fuentes
    })

# 🔹 ORDENAR: últimas subidas primero
peliculas_items.sort(key=lambda x: x["_created"], reverse=True)

# 🔹 limpiar campo interno
for item in peliculas_items:
    item.pop("_created", None)

new_peliculas_index = {
    "type": "peliculas",
    "total": len(peliculas_items),
    "items": peliculas_items
}

# =========================
# 🔹 EXPORTAR SERIES
# =========================

series_items = []

for doc in db.collection("series").stream():
    data = doc.to_dict()

    if data.get("estado") != "activo":
        continue

    temporadas = data.get("temporadas", {})
    if not temporadas:
        continue

    series_items.append({
        "_created": doc.create_time.timestamp(),  # 🔹 SOLO para ordenar
        "id": f"s_{data.get('tmdb_id')}",
        "tmdb_id": data.get("tmdb_id"),
        "nombre": data.get("nombre"),
        "poster": data.get("portada"),
        "categorias": data.get("categorias", []),
        "temporadas": temporadas
    })

# 🔹 ORDENAR: últimas subidas primero
series_items.sort(key=lambda x: x["_created"], reverse=True)

# 🔹 limpiar campo interno
for item in series_items:
    item.pop("_created", None)

new_series_index = {
    "type": "series",
    "total": len(series_items),
    "items": series_items
}

# =========================
# 🔹 COMPARAR CON ANTERIORES
# =========================

old_peliculas = load_json(PELIS_FILE)
old_series = load_json(SERIES_FILE)

pelis_changed = file_hash(new_peliculas_index) != file_hash(old_peliculas) if old_peliculas else True
series_changed = file_hash(new_series_index) != file_hash(old_series) if old_series else True

# =========================
# 🔹 SI HAY CAMBIOS → VERSION +1
# =========================

if pelis_changed or series_changed:
    new_version = current_version + 1

    new_peliculas_index["version"] = new_version
    new_series_index["version"] = new_version

    save_json(PELIS_FILE, new_peliculas_index)
    save_json(SERIES_FILE, new_series_index)
    save_json(VERSION_FILE, {"version": new_version})

    print(f"🚀 Catálogo actualizado → versión {new_version}")
else:
    print("⏸️ No hubo cambios, versión no modificada")

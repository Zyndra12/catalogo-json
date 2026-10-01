import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate(r"C:\migracion_firestore\firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

print("🔎 Contando series...")
count = 0
for doc in db.collection("series").stream():
    count += 1
    if count % 500 == 0:
        print(f"   ... {count} docs")

print(f"✅ Total: {count} series")
import firebase_admin
from firebase_admin import credentials, firestore

# Path to your service account key JSON file
cred = credentials.Certificate("/home/swamyaranjan/Documents/diet-analysis-backend/ServiceAccountKey1.json")

# Initialize Firebase app
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

# Example: Add a document to a collection
doc_ref = db.collection("users").document("user1")
doc_ref.set({
    "name": "Swamya",
    "email": "myselfswamya@gmail.com",
    "role": "Owner"
    
})

print("Document successfully written!")

# Example: Read document
doc = doc_ref.get()
if doc.exists:
    print("Document Data:", doc.to_dict())
else:
    print("No such document found!")

# Example: Query Firestore
users_ref = db.collection("users")
docs = users_ref.stream()
for doc in docs:
    print(f"{doc.id} => {doc.to_dict()}")

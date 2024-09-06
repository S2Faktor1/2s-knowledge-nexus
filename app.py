import os
import hashlib
from flask import Flask, request, render_template, jsonify
import openai
import logging
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
import subprocess
import sys
from werkzeug.utils import secure_filename
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Loading environment variables
load_dotenv()

# Inicializace Flask aplikace
app = Flask(__name__)

# Setting variables for OpenAI API
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2023-03-15-preview"
openai.api_key = os.getenv("AZURE_OPENAI_KEY")

# Blob Storage configuration
blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AZURE_BLOB_CONNECTION_STRING"))
container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME")

# Lokální složky
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed-data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Logging settings
logging.basicConfig(level=logging.INFO)

# Global variable for storing document embeddings
document_embeddings = []

# Function to read all JSON files from a Blob Storage container and create embeddings
def load_and_process_documents():
    global document_embeddings
    document_embeddings = []
    
    # Access the Blob container
    container_client = blob_service_client.get_container_client(container_name)

    # List all blobs in the container
    blob_list = container_client.list_blobs()
    
    # Process each blob (JSON file)
    for blob in blob_list:
        if blob.name.endswith(".json"):
            blob_client = container_client.get_blob_client(blob.name)
            blob_data = blob_client.download_blob().readall()
            json_documents = json.loads(blob_data.decode('utf-8'))
            
            # Process the documents and add them to the embedding list
            document_embeddings.extend(process_json_documents(json_documents))

# Functions for processing individual documents and creating embeddings
def process_json_documents(json_documents):
    embeddings = []
    for section in json_documents.get("sections", []):
        content = ""
        if isinstance(section.get("content"), list):  # Check if the 'content' list is
            content = " ".join([para.get("text", "") for para in section["content"] if "text" in para])
        elif isinstance(section.get("content"), str):  # If it's a string, use this content directly
            content = section["content"]
        
        if content:  # If we have some content, we create an embedding
            embedding = generate_embeddings(content)
            embeddings.append({
                "section_title": section.get("section_title", "Unknown Section"),
                "embedding": embedding,
                "content": content
            })
    return embeddings

def generate_embeddings(content):
    response = openai.Embedding.create(
        input=content,
        engine="testDep3"  # Zadej správný název modelu na Azure
    )
    return response['data'][0]['embedding']

# Functions for finding the best match using embeddings
def find_best_match(query_embedding, document_embeddings):
    similarities = cosine_similarity([query_embedding], [doc['embedding'] for doc in document_embeddings])
    best_match_idx = np.argmax(similarities)
    return document_embeddings[best_match_idx]

# Loading and processing documents from Blob Storage at application startup
load_and_process_documents()

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Function to check if a file with the same name already exists in Blob Storage
def file_exists_in_blob_storage(file_name):
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
        return blob_client.exists()  # Returns True if the blob exists, False otherwise
    except Exception as e:
        print(f"Error checking file existence in Blob Storage: {e}")
        return False

# Function to upload file to Blob Storage
def upload_to_blob_storage(blob_name, file_path):
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        print(f"File '{blob_name}' uploaded to Blob Storage.")
    except Exception as e:
        print(f"Error uploading file to Blob Storage: {e}")

        
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "Invalid input"}), 400

    try:
        # Creating an embedding for a query
        query_embedding = generate_embeddings(prompt)
        
        # Find the best match to the document
        best_match = find_best_match(query_embedding, document_embeddings)

        return jsonify({"message": best_match["content"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Endpoint for uploading Word documents and converting to JSON in Blob Storage
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Getting a safe filename
    filename = secure_filename(file.filename)
    json_filename = os.path.splitext(filename)[0] + ".json"
    
    # Check if a file with this name already exists in Blob Storage
    if file_exists_in_blob_storage(json_filename):
        return jsonify({"error": f"File '{json_filename}' already exists in Blob Storage."}), 400

    # If the file does not exist, continue processing it
    try:
        #  Saving a file to temporary storage
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        print(f"File saved to: {file_path}")
    except Exception as e:
        print(f"Error saving file: {e}")
        return jsonify({"error": str(e)}), 500

    # Running a script to process a Word document (conversion to JSON)
    try:
        result = subprocess.run([sys.executable, 'WordDocPrepBlob.py', file_path], capture_output=True, text=True)
        # print(f"Subprocess output: {result.stdout}")  
        # print(f"Subprocess error: {result.stderr}")   
        if result.returncode != 0:
            print(f"Script error: {result.stderr}")
            return jsonify({"error": result.stderr}), 500

        # Uploading a JSON file to Blob Storage
        json_file_path = os.path.join(PROCESSED_FOLDER, json_filename)
        upload_to_blob_storage(json_filename, json_file_path)

        # Deleting files after processing
        os.remove(file_path) 
        os.remove(json_file_path)  

        return jsonify({"message": "File uploaded and processed successfully."})
    except Exception as e:
        print(f"Error running script: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

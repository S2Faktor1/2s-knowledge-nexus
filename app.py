from flask import Flask, request, render_template, jsonify
import openai
import logging
from dotenv import load_dotenv
import os
import json
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

#Loading environment variables
load_dotenv()

# Inicializace Flask aplikace
app = Flask(__name__)

# Setting variables for OpenAI API
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2023-03-15-preview"
openai.api_key = os.getenv("AZURE_OPENAI_KEY")

# Logging settings
logging.basicConfig(level=logging.INFO)

# Global variable for storing document embeddings
document_embeddings = []

# Function to read all JSON files from a directory and create embeddings
def load_and_process_documents():
    global document_embeddings
    document_embeddings = []
    
    # Path to the file directory
    directory = 'processed-data'
    
    # Go through all the files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".json"):  # Load only JSON files
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                json_documents = json.load(f)
                # Process the documents and add them to the embedding list
                document_embeddings.extend(process_json_documents(json_documents))

# Functions for processing individual documents and creating embeddings
def process_json_documents(json_documents):
    embeddings = []
    for section in json_documents.get("sections", []):
        content = ""
        if isinstance(section.get("content"), list):  # Check if the 'content' list is
            # Add a check if each item contains the key 'text'
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
        engine="testDep3" 
    )
    return response['data'][0]['embedding']

# Functions for finding the best match using embeddings
def find_best_match(query_embedding, document_embeddings):
    similarities = cosine_similarity([query_embedding], [doc['embedding'] for doc in document_embeddings])
    best_match_idx = np.argmax(similarities)
    return document_embeddings[best_match_idx]

# Loading and processing documents at application startup
load_and_process_documents()

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint for chatting with AI
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

if __name__ == '__main__':
    app.run(debug=True)

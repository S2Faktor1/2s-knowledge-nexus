import openai
import json
import numpy as np
from dotenv import load_dotenv
import sys
import os
from PIL import Image
import requests
from io import BytesIO

# Load environment variables from the .env file
load_dotenv()

# Get the OpenAI API key from the environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

def load_processed_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_image_vector(image_path):
    # Load image from file path
    image = Image.open(image_path)

    # Convert image to required format
    # For instance, resize or normalize if needed
    # image = image.resize((224, 224))

    # Use an image embedding model (e.g., OpenAI's CLIP or similar model)
    # Here, we'll use a placeholder function; replace with actual model inference
    response = openai.Image.create(input=image, model="image-embedding-model")
    vector = response['data'][0]['embedding']

    return vector

def process_images(data):
    image_vectors = []
    for section in data['sections']:
        for content in section['content']:
            if content['type'] == 'image':
                image_path = content['path']
                vector = create_image_vector(image_path)
                image_vectors.append({
                    'section_title': section['section_title'],
                    'image_path': image_path,
                    'vector': vector
                })
    return image_vectors

def create_vectors(data):
    text_vectors = []
    for section in data['sections']:
        section_text = section['section_title'] + " " + " ".join(
            [content['text'] for content in section['content'] if content['type'] == 'paragraph']
        )
        
        # Call OpenAI API to get the embedding vector for the section text
        response = openai.Embedding.create(input=section_text, model="text-embedding-ada-002")
        vector = response['data'][0]['embedding']
        
        text_vectors.append({
            'section_title': section['section_title'],
            'vector': vector
        })
    
    # Process images separately
    image_vectors = process_images(data)
    
    return text_vectors, image_vectors

def save_vectors(vectors, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(vectors, f, ensure_ascii=False, indent=4)

def process_file(json_file):
    data = load_processed_data(json_file)
    text_vectors, image_vectors = create_vectors(data)
    
    # Save text and image vectors to separate files
    text_output_file = f'text_vectors_{os.path.basename(json_file)}'
    image_output_file = f'image_vectors_{os.path.basename(json_file)}'
    
    save_vectors(text_vectors, text_output_file)
    save_vectors(image_vectors, image_output_file)
    
    print(f"Text vectors saved to {text_output_file}")
    print(f"Image vectors saved to {image_output_file}")

def process_directory(directory_path):
    json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
    
    for json_file in json_files:
        file_path = os.path.join(directory_path, json_file)
        print(f"Processing file: {json_file}")
        process_file(file_path)

def main():
    if len(sys.argv) < 2:
        print("Usage: python your_script.py <directory> [<file1.json> ...]")
        sys.exit(1)

    path = sys.argv[1]
    
    if os.path.isfile(path):
        # Process a single JSON file
        process_file(path)
    elif os.path.isdir(path):
        # Process all JSON files in the directory
        process_directory(path)
    else:
        print(f"Path '{path}' is neither a file nor a directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()

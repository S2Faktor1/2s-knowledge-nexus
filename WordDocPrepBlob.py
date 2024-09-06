import os
import io
import sys
import json
from docx import Document
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables for Blob Storage
load_dotenv()

blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AZURE_BLOB_CONNECTION_STRING"))
container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME")

def save_image(image, file_name):
    """Saves an image to the processed-data/images directory."""
    images_dir = 'processed-data/images'
    os.makedirs(images_dir, exist_ok=True)
    image_path = os.path.join(images_dir, file_name)
    with open(image_path, "wb") as img_file:
        img_file.write(image)
    return image_path

def process_document(file_path):
    """Processes a Word document and extracts text and metadata."""
    doc = Document(file_path)
    data = {
        "title": "",
        "metadata": {
            "author": "",
            "creation_date": "",
            "version": ""
        },
        "sections": []
    }

    # Extract metadata
    core_props = doc.core_properties
    data["title"] = core_props.title
    data["metadata"]["author"] = core_props.author
    data["metadata"]["creation_date"] = core_props.created.strftime('%Y-%m-%d %H:%M:%S') if core_props.created else ""
    data["metadata"]["version"] = core_props.version

    # Extract content
    section = None
    for para in doc.paragraphs:
        if para.style.name.startswith('Heading'):
            section = {
                "section_title": para.text,
                "content": []
            }
            data["sections"].append(section)
        elif para.text.strip() == "":
            continue
        else:
            if section:
                section["content"].append({"type": "paragraph", "text": para.text})
    
    return data

def upload_to_blob(blob_name, file_path):
    """Uploads a file to Azure Blob Storage."""
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    print(f"Uploaded {blob_name} to Blob Storage.")

def process_directory(directory_path, file_names=None):
    """Processes all Word documents in the directory and converts them to JSON."""
    files = file_names or [f for f in os.listdir(directory_path) if f.endswith('.docx')]
    results = {}

    processed_dir = 'processed-data'
    os.makedirs(processed_dir, exist_ok=True)
    
    for file_name in files:
        file_path = os.path.join(directory_path, file_name)
        if os.path.isfile(file_path):
            results[file_name] = process_document(file_path)
            
            # Save the processed data with the same name as the Word file
            base_name, _ = os.path.splitext(file_name)
            processed_file_name = f"{base_name}.json"
            processed_file_path = os.path.join(processed_dir, processed_file_name)
            
            with open(processed_file_path, 'w', encoding='utf-8') as f:
                json.dump(results[file_name], f, ensure_ascii=False, indent=4)
            
            # Upload the processed JSON to Blob Storage
            upload_to_blob(processed_file_name, processed_file_path)
    
    return results

def main():
    """Main function for processing a Word document."""
    if len(sys.argv) < 2:
        print("Usage: python WordDocPrepBlob.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    
    if not os.path.isfile(file_path):
        print(f"File '{file_path}' does not exist.")
        sys.exit(1)

    # Process the document and upload to Blob Storage
    results = process_directory(os.path.dirname(file_path), [os.path.basename(file_path)])
    for file_name, data in results.items():
        print(f"\nProcessed {file_name}:")
        print(data)

if __name__ == "__main__":
    main()

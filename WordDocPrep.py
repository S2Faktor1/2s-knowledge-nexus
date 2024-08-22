import os
import sys
import json
from docx import Document
from docx.shared import Inches
from datetime import datetime

def save_image(image, file_name):
    """Saves an image to the processed-data/images directory."""
    images_dir = 'processed-data/images'
    os.makedirs(images_dir, exist_ok=True)
    image_path = os.path.join(images_dir, file_name)
    with open(image_path, "wb") as img_file:
        img_file.write(image)
    return image_path

def process_document(file_path):
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

    # Metadata extraction (Example: Placeholder values; adjust as needed)
    core_props = doc.core_properties
    data["title"] = core_props.title
    data["metadata"]["author"] = core_props.author
    data["metadata"]["creation_date"] = core_props.created.strftime('%Y-%m-%d %H:%M:%S') if core_props.created else ""
    data["metadata"]["version"] = core_props.version

    section = None
    for i, para in enumerate(doc.paragraphs):
        if para.style.name.startswith('Heading'):
            # Determine header level
            level = int(para.style.name.replace('Heading ', ''))
            section = {
                "section_title": para.text,
                "content": []
            }
            data["sections"].append(section)
        elif para.text.strip() == "":
            continue
        else:
            if section:
                # Detect if the paragraph is a list
                if para.style.name == 'List Bullet' or para.style.name == 'List Number':
                    content_type = "list"
                    items = section.get("content", [])
                    if not items or items[-1]["type"] != "list":
                        items.append({"type": "list", "items": []})
                    items[-1]["items"].append(para.text)
                else:
                    content_type = "paragraph"
                    section["content"].append({"type": content_type, "text": para.text})
        
        # Handling images within the document
        for rel in para._element.xpath('.//a:blip'):
            image = rel.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            image_part = doc.part.related_parts[image]
            image_data = image_part.blob
            image_name = f"{os.path.splitext(os.path.basename(file_path))[0]}_image_{i}.png"
            image_path = save_image(image_data, image_name)
            
            if section:
                section["content"].append({"type": "image", "image_path": image_path})
    
    return data

def process_directory(directory_path, file_names=None):
    files = file_names or [f for f in os.listdir(directory_path) if f.endswith('.docx')]
    results = {}
    
    # Ensure processed-data directory exists
    processed_dir = 'processed-data'
    os.makedirs(processed_dir, exist_ok=True)
    
    for file_name in files:
        file_path = os.path.join(directory_path, file_name)
        if os.path.isfile(file_path):
            print(f"Processing file: {file_name}")
            results[file_name] = process_document(file_path)
            
            # Save the processed data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name, _ = os.path.splitext(file_name)
            processed_file_name = f"{base_name}_{timestamp}.json"
            processed_file_path = os.path.join(processed_dir, processed_file_name)
            
            with open(processed_file_path, 'w', encoding='utf-8') as f:
                json.dump(results[file_name], f, ensure_ascii=False, indent=4)
            
            print(f"Saved processed data to {processed_file_path}")
    
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python doc_prep.py <directory> [<file1> <file2> ...]")
        sys.exit(1)

    directory_path = sys.argv[1]
    file_names = sys.argv[2:] if len(sys.argv) > 2 else None

    if not os.path.isdir(directory_path):
        print(f"Directory '{directory_path}' does not exist.")
        sys.exit(1)

    results = process_directory(directory_path, file_names)
    for file_name, data in results.items():
        print(f"\nProcessed {file_name}:")
        print(data)

if __name__ == "__main__":
    main()

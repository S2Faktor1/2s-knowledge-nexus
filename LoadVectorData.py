import os
import json
import sys

# Directory containing the vector data files
VECTOR_DATA_DIR = "vector-data"

def load_all_vectors(vector_data_dir):
    vector_data = {}
    
    # Iterate over all files in the directory
    for file_name in os.listdir(vector_data_dir):
        if file_name.endswith('.json'):
            file_path = os.path.join(vector_data_dir, file_name)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Store the data in a dictionary with the file name as the key
            vector_data[file_name] = data
    
    return vector_data

def reload_vectors(vector_data_dir):
    print("Reloading all vector data files...")
    return load_all_vectors(vector_data_dir)

def main():
    if len(sys.argv) != 2:
        print("Usage: python your_script.py <all|reload>")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "all":
        vectors = load_all_vectors(VECTOR_DATA_DIR)
        print("Vector data loaded successfully.")
        # Print some details about the loaded data
        print(f"Loaded {len(vectors)} vector files.")
        for file_name, data in vectors.items():
            print(f"File: {file_name}, Number of vectors: {len(data)}")
    elif command == "reload":
        vectors = reload_vectors(VECTOR_DATA_DIR)
        print("Vector data reloaded successfully.")
        # Print some details about the reloaded data
        print(f"Loaded {len(vectors)} vector files.")
        for file_name, data in vectors.items():
            print(f"File: {file_name}, Number of vectors: {len(data)}")
    else:
        print("Invalid command. Use 'all' to load vectors or 'reload' to reload vectors.")
        sys.exit(1)

if __name__ == "__main__":
    main()

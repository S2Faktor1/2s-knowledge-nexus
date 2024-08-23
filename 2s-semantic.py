import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Directory containing the vector data files
VECTOR_DATA_DIR = "vector-data"

def load_all_vectors(vector_data_dir):
    vector_data = []
    document_titles = []
    
    # Iterate over all files in the directory
    for file_name in os.listdir(vector_data_dir):
        if file_name.endswith('.json'):
            file_path = os.path.join(vector_data_dir, file_name)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for doc in data:
                        if 'vector' in doc and 'section_title' in doc:
                            vector_data.append(doc['vector'])
                            document_titles.append(doc['section_title'])
                        else:
                            print(f"Warning: Missing 'vector' or 'section_title' in {file_path}")
            except Exception as e:
                print(f"Error loading file {file_path}: {e}")
    
    if not vector_data or not document_titles:
        raise ValueError("No valid vectors or titles were loaded.")
    
    return np.array(vector_data), document_titles

# Function to simulate vectorization of the query
def get_query_vector(query, vector_dim):
    # Placeholder function: replace this with your actual query vectorization
    query_vectors = {
        "how does the candidate app work?": [0.1, 0.2, 0.3],
        "what is this data about?": [0.4, 0.5, 0.6],
        "I'm not able to gain access to btp": [0.7, 0.8, 0.9]
    }
    vector = query_vectors.get(query)
    if vector is None:
        print(f"Warning: Query '{query}' not recognized. Using default vector.")
        vector = [0.0] * vector_dim  # Default vector of correct size
    return np.array(vector)

# Function to perform semantic search
def semantic_search(query_vector, document_vectors, document_titles):
    if query_vector.shape[0] != document_vectors.shape[1]:
        raise ValueError("Query vector and document vectors must have the same dimensions.")
    
    similarities = cosine_similarity([query_vector], document_vectors)
    most_similar_index = np.argmax(similarities)
    return document_titles[most_similar_index], similarities[0][most_similar_index]

def main():
    try:
        # Load vectors from JSON files
        document_vectors, document_titles = load_all_vectors(VECTOR_DATA_DIR)
        print("Vectors loaded successfully.")
        print(f"Document vectors shape: {document_vectors.shape}")
    except Exception as e:
        print(f"Failed to load vectors: {e}")
        return
    
    # Get the dimension of the document vectors
    vector_dim = document_vectors.shape[1]
    print(f"Vector dimension: {vector_dim}")

    print("Semantic Search Console")
    print("Type 'exit' to quit.")
    
    while True:
        query = input("Enter your search query: ")
        if query.lower() == 'exit':
            break
        
        query_vector = get_query_vector(query, vector_dim)
        print(f"Query vector shape: {query_vector.shape}")
        
        try:
            document_title, similarity = semantic_search(query_vector, document_vectors, document_titles)
            print(f"Most similar document: {document_title} (Similarity: {similarity:.4f})")
        except Exception as e:
            print(f"Error during semantic search: {e}")

if __name__ == "__main__":
    main()

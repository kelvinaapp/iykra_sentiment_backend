import faiss
import numpy as np
import pandas as pd
from langchain_openai import OpenAIEmbeddings

# Load embeddings and data
def load_embeddings_and_data(embeddings_path, data_path):
    """Loads embeddings and associated data."""
    embeddings = np.load(embeddings_path)
    data = pd.read_csv(data_path)
    return embeddings, data

# Create FAISS index
def create_faiss_index(embeddings):
    """Creates a FAISS index from embeddings."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index

# Save FAISS index
def save_faiss_index(index, output_path):
    """Saves a FAISS index to disk."""
    faiss.write_index(index, output_path)

# Process multiple datasets to create FAISS index
def prepare_faiss_index(embeddings_paths, data_paths, index_output_paths):
    """Loads embeddings and data, creates FAISS index, and saves it for multiple datasets."""
    for embeddings_path, data_path, index_output_path in zip(embeddings_paths, data_paths, index_output_paths):
        print(f"Processing embeddings and data from {embeddings_path} and {data_path}...")

        embeddings, data = load_embeddings_and_data(embeddings_path, data_path)
        
        print(f"Creating FAISS index for {data_path}...")
        index = create_faiss_index(embeddings)

        print(f"Saving FAISS index to {index_output_path}...")
        save_faiss_index(index, index_output_path)

        print(f"FAISS index preparation for {data_path} complete.\n")

# Example usage
if __name__ == "__main__":
    # Paths for embeddings and data files
    embeddings_paths = [
        "data/processed_product_catalog_embeddings.npy", 
        "data/komentar_instagram_embeddings.npy", 
        "data/info_produk_embeddings.npy",  
        "data/amazon_review_combined3_embeddings.npy", 
        "data/basic_info_instagram_embeddings.npy"  
    ]

    data_paths = [
        "data/processed_product_catalog.csv",  
        "data/komentar_instagram.csv",  
        "data/info_produk.csv",  
        "data/amazon_review_combined3.csv",  
        "data/basic_info_instagram.csv"  
    ]
    
    index_output_paths = [
        "data/product_catalog_faiss.index",  
        "data/komentar_instagram_faiss.index",  
        "data/info_produk_faiss.index",  
        "data/amazon_review_combined3_faiss.index",  
        "data/basic_info_instagram_faiss.index"  
    ]
    
    # Call the function to process multiple datasets and create FAISS indices
    prepare_faiss_index(embeddings_paths, data_paths, index_output_paths)

import os
import tempfile
import pandas as pd
import numpy as np
from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from generate import generate_response_from_api

data_paths = [
    r"C:\IYKRA\10chatbot - Copy\data\product-catalog.csv",
    r"C:\IYKRA\10chatbot - Copy\data\komentar_instagram.csv",
    r"C:\IYKRA\10chatbot - Copy\data\info_produk.csv",
    r"C:\IYKRA\10chatbot - Copy\data\amazon_review_combined3.csv",
    r"C:\IYKRA\10chatbot - Copy\data\basic_info_instagram.csv"
]

# Check if files exist
def check_files():
    """Checks for the existence of all required files."""
    for key, path in data_paths.items():
        if os.path.exists(path):
            print(f"File ditemukan: {path}")
        else:
            print(f"File tidak ditemukan: {path}")

# Clean text function
def clean_text(text):
    """Cleans text by removing unnecessary characters."""
    import re
    text = re.sub(r'[^a-zA-Z0-9\s]', '', str(text))
    return text.lower().strip()

# Process each CSV file
def process_csv_file(input_path, columns_to_use):
    """Loads CSV, cleans text, and returns processed DataFrame."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file {input_path} does not exist.")

    df = pd.read_csv(input_path)

    if not all(col in df.columns for col in columns_to_use):
        raise ValueError(f"Required columns {columns_to_use} not found in {input_path}.")

    for col in columns_to_use:
        clean_col = f"cleaned_{col}"
        df[clean_col] = df[col].apply(clean_text)

    return df

# Generate document embeddings
def getDocEmbeds(file, filename):
    """Generates document embeddings and saves them as a FAISS index."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp_file:
        tmp_file.write(file)
        tmp_file_path = tmp_file.name

    loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8")
    data = loader.load()

    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(data, embeddings)

    index_path = f"{filename}.index"
    vector_store.save_local(index_path)
    os.remove(tmp_file_path)

    return vector_store

# Conversational chat
def conversational_chat(query, chain, dataset_response=None):
    """Handles conversational queries using a chain and falls back to OpenAI if no result is found."""
    try:
        # First, attempt to get a response from the conversational chain (dataset)
        result = chain({"question": query, "chat_history": []})
        answer = result.get("answer", None)
        
        # If no answer from dataset, fall back to OpenAI API
        if not answer:
            answer = generate_response_from_api(query)
        
        return answer
    except Exception as e:
        print(f"Error: {e}")
        return generate_response_from_api(query)

# Main function to process and embed files
def main():
    check_files()

    for key, path in data_paths.items():
        if key == "product_catalog":
            df = process_csv_file(path, columns_to_use=["name"])
        elif key == "komentar_instagram":
            df = process_csv_file(path, columns_to_use=["judul"])
        elif key == "info_produk":
            df = process_csv_file(path, columns_to_use=["product_summary"])
        elif key == "amazon_review":
            df = process_csv_file(path, columns_to_use=["comment"])
        elif key == "basic_info_instagram":
            df = process_csv_file(path, columns_to_use=["judul"])

        output_path = os.path.splitext(path)[0] + "_processed.csv"
        df.to_csv(output_path, index=False)
        print(f"Processed file saved: {output_path}")

if __name__ == "__main__":
    main()

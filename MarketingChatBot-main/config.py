import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API Key and Model Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-3.5-turbo"
TEMPERATURE = 0.0

# Dataset File Paths
CSV_FILE_PATHS = {
    "product_catalog": "data/product_catalog.csv",
    "komentar_instagram": "data/komentar_instagram.csv",
    "info_produk": "data/info_produk.csv",
    "amazon_review": "data/amazon_review_combined3.csv",
    "basic_info_instagram": "data/basic_info_instagram.csv",
}

# Function to validate API Key and check dataset files
def validate_configuration():
    if not OPENAI_API_KEY:
        raise ValueError("API Key untuk OpenAI tidak ditemukan. Pastikan telah diset di .env file.")

    missing_files = [key for key, path in CSV_FILE_PATHS.items() if not os.path.exists(path)]
    if missing_files:
        raise FileNotFoundError(f"File berikut tidak ditemukan: {', '.join(missing_files)}")

    print("Semua konfigurasi validasi berhasil!")

# Example usage
if __name__ == "__main__":
    try:
        validate_configuration()
    except Exception as e:
        print(f"Error: {e}")

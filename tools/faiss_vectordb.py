import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from uuid import uuid4
from tqdm import tqdm
import tiktoken

from dotenv import load_dotenv
import os
from db.database import engine, get_db_session, DATABASE_URL
from sqlalchemy import text


load_dotenv()

if not os.environ.get("LANGSMITH_API_KEY"):
    os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
    os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING")

def extract_document():
    db = get_db_session()
    
    documents = []

    try:
        # Query Product_Catalog
        products = db.execute(text("""
            SELECT 
                product_id, product_name, brand, subcategory, color, gender_orientation, 
                care_instructions, origin, sole_material, upper_material, product_lifecycle_status
            FROM Product_Catalog
            WHERE product_lifecycle_status = 'Active'
        """))

        for product in products:
            documents.append(
                Document(
                    page_content=f"{product.product_name} {product.brand} {product.subcategory} {product.color} {product.gender_orientation} {product.care_instructions} {product.origin} {product.sole_material} {product.upper_material} {product.product_lifecycle_status}",
                    metadata={
                        "source": "product_catalog",
                        "product_id": product.product_id,
                        "brand": product.brand,
                        "subcategory": product.subcategory,
                        "color": product.color,
                        "gender_orientation": product.gender_orientation
                    }
                )
            )

        # Query Reviewed_Product
        reviews = db.execute(text("""
            SELECT 
                customer_review_id, review_text, keyword_tags, aspect_sentiments, 
                username, nama_produk, brand
            FROM Reviewed_Product
        """))

        for review in reviews:
            documents.append(
                Document(
                    page_content=f"{review.review_text} {' '.join(review.keyword_tags or [])} {review.aspect_sentiments} {review.username} {review.nama_produk} {review.brand}",
                    metadata={
                        "source": "reviewed_product",
                        "review_id": review.customer_review_id,
                        "username": review.username,
                        "product_name": review.nama_produk,
                        "brand": review.brand
                    }
                )
            )

        # Query Social_Media
        social_media_posts = db.execute(text("""
            SELECT 
                social_media_post_id, platform, post_text, hashtags, collabs, collabs_status, jenis_konten, brand
            FROM Social_Media
        """))

        for post in social_media_posts:
            documents.append(
                Document(
                    page_content=f"{post.platform} {post.post_text} {' '.join(post.hashtags or [])} {post.collabs} {post.collabs_status} {post.jenis_konten} {post.brand}",
                    metadata={
                        "source": "social_media",
                        "post_id": post.social_media_post_id,
                        "platform": post.platform,
                        "collabs_status": post.collabs_status,
                        "content_type": post.jenis_konten,
                        "brand": post.brand
                    }
                )
            )

        # Query Sentiment_Social_Media
        sentiments = db.execute(text("""
            SELECT 
                id_post, comment
            FROM Sentiment_Social_Media
        """))

        for sentiment in sentiments:
            documents.append(
                Document(
                    page_content=sentiment.comment,
                    metadata={
                        "source": "sentiment_social_media",
                        "post_id": sentiment.id_post
                    }
                )
            )
        
        return documents
    
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        db.close()

def split_and_tokenizer(documents):
    print("\n=== Splitting Documents ===")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    split_docs = text_splitter.split_documents(documents)
    print(f"+ Created {len(split_docs):,} document chunks")
    
    print("\n=== Analyzing Tokens ===")
    # Initialize tokenizer
    tokenizer = tiktoken.get_encoding("cl100k_base")
    max_tokens = 8000
    
    # Calculate tokens for all texts
    total_tokens = 0
    truncated_count = 0
    
    print("* Counting tokens and truncating if needed...")
    for doc in tqdm(split_docs, desc="Processing texts", unit="doc"):
        tokens = len(tokenizer.encode(doc.page_content))
        total_tokens += tokens
        
        # Truncate if needed
        if tokens > max_tokens:
            truncated_count += 1
            tokens = tokenizer.encode(doc.page_content)[:max_tokens]
            doc.page_content = tokenizer.decode(tokens)
    
    avg_tokens = total_tokens / len(split_docs)
    print(f"+ Average tokens per text: {avg_tokens:.1f}")
    if truncated_count > 0:
        print(f"! {truncated_count:,} texts were truncated to {max_tokens:,} tokens")
    
    return split_docs, tokenizer

def process_batch(batch_docs):
    """Process a batch of documents"""
    texts = [doc.page_content for doc in batch_docs]
    metadatas = [doc.metadata for doc in batch_docs]
    batch_tokens = sum(len(tokenizer.encode(text)) for text in texts)
    
    vdb = FAISS(
        embedding_function=embeddings,
        index=faiss.IndexFlatL2(dimension),
        docstore=InMemoryDocstore(),
        index_to_docstore_id={}
    )
    
    return vdb.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas
    ), batch_tokens

def create_vector_db(documents):
    
    print("\n=== Loading Documents ===")
    documents = extract_document()
    print(f"+ Found {len(documents):,} documents")
    
    split_docs, tokenizer = split_and_tokenizer(documents)
    
    print("\n=== Creating Embeddings ===")
    dimension = 3072
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    
    # Process in batches for better performance
    batch_size = 200
    total_batches = (len(split_docs) + batch_size - 1) // batch_size
    print(f"* Processing {total_batches:,} batches (batch size: {batch_size:,})")
    
    # Initialize progress bar
    pbar = tqdm(total=total_batches,
                desc="Creating embeddings",
                unit="batch",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]")
    
    # Process all batches
    vector_store = None
    total_processed_tokens = 0
    
    for i in range(0, len(split_docs), batch_size):
        batch = split_docs[i:i+batch_size]
        
        if vector_store is None:
            # First batch initializes the vector store
            vector_store, batch_tokens = process_batch(batch)
        else:
            # Subsequent batches are merged
            new_vectorstore, batch_tokens = process_batch(batch)
            vector_store.merge_from(new_vectorstore)
        
        # Update progress
        total_processed_tokens += batch_tokens
        pbar.update(1)
        pbar.set_postfix({
            "tokens_processed": f"{total_processed_tokens:,}",
            "avg_tokens/batch": f"{total_processed_tokens/(pbar.n):,.0f}"
        })
    
    print(f"\n+ Vector store creation completed!")
    print(f"+ Total tokens processed: {total_processed_tokens:,}")
    print(f"+ Average tokens per batch: {total_processed_tokens/total_batches:,.0f}")
    
    return vector_store

def save_vector_db(vector_store: FAISS, path: str = "vector_db"):
    print(f"\n=== Saving Vector Store ===")
    vector_store.save_local(path)
    print("Vector store saved successfully")
    
def load_vector_db(path: str = "vector_db"):
    
    print(f"\n=== Loading Vector Store ===")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    
    vector_store = FAISS.load_local(
        folder_path=path,
        embeddings=embeddings,
        allow_dangerous_deserialization=True  # Safe because we created this file
    )
    print("Vector store loaded successfully\n")
    return vector_store


if __name__ == "__main__":
    
    vector_store_path = "vector_db"
    
    if os.path.exists(vector_store_path):
        vector_store = load_vector_db(vector_store_path)
        
        results = vector_store.similarity_search(
            "Blue Casual Nike Sandals",
            k=3,
        )
        for res in results:
            print(f"* {res.page_content} [{res.metadata}]")
    else:
        documents = extract_document()
        
        print("total documents: ", len(documents))
        
        if(documents is not None):
            print("==== Initializing Vector DB ====")
            vector_store = create_vector_db(documents)
            print("vector_store: ", vector_store)
            
            print("==== Saving Vector DB ====")
            if(vector_store is not None):
                save_vector_db(vector_store, vector_store_path)
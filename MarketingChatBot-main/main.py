import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from generate import generate_response
from utils import getDocEmbeds, conversational_chat
from streamlit_chat import message
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI  
from langchain.prompts import SystemMessagePromptTemplate
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema import SystemMessage
from prompt_engineering import get_system_prompt, get_task_prompt

# Set Streamlit page configuration
st.set_page_config(layout="wide", page_icon="💬", page_title="MarketingBot")

# Load environment variables
load_dotenv()

# Validate API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("API Key untuk OpenAI tidak ditemukan. Pastikan telah diset di file .env.")
    st.stop()
    
# Set CSV file paths
CSV_FILE_PATHS = {
    "product_catalog": "data/product_catalog.csv",
    "komentar_instagram": "data/komentar_instagram.csv",
    "info_produk": "data/info_produk.csv",
    "amazon_review": "data/amazon_review_combined3.csv",
    "basic_info_instagram": "data/basic_info_instagram.csv",
}

# Function to check and load CSV files
def load_and_process_csv_files():
    data = {}
    for key, path in CSV_FILE_PATHS.items():
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File tidak ditemukan: {path}")
            data[key] = pd.read_csv(path)
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memuat file {key}: {e}")
            st.stop()
    return data

# Function to initialize chatbot pipeline
def initialize_pipeline():
    try:
        # Load and preprocess CSV files
        data = load_and_process_csv_files()

        # Load document embeddings
        doc_path = CSV_FILE_PATHS["product_catalog"]
        with open(doc_path, "rb") as uploaded_file:
            file = uploaded_file.read()
        vectors = getDocEmbeds(file, doc_path)

        # Load system prompt and add to memory
        system_prompt = get_system_prompt().template
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_memory=10
        )
        memory.chat_memory.add_message(SystemMessage(content=system_prompt))

        # Add task-specific prompt if available
        task_prompt = get_task_prompt("real_time_insights")  # Example question type
        if task_prompt:
            memory.chat_memory.add_message(SystemMessage(content=task_prompt))

        # Initialize conversational retrieval chain
        chain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo"),
            retriever=vectors.as_retriever(),
            memory=memory
        )

        return chain
    except Exception as e:
        st.error(f"Error saat inisialisasi chatbot: {str(e)}")
        st.stop()

# Main function
def main():
    # Session state initialization
    if "chain" not in st.session_state:
        st.session_state["chain"] = initialize_pipeline()

    if "history" not in st.session_state:
        st.session_state["history"] = []

    # Chat interface
    st.markdown("<h1 style='text-align: center;'>MarketingBot</h1>", unsafe_allow_html=True)
    response_container = st.container()
    input_container = st.container()

    with input_container:
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "",
                placeholder="Type your question here...",
                key="input"
            )
            submit_button = st.form_submit_button(label="Send")

            if submit_button and user_input:
                chain = st.session_state["chain"]

                # Generate response
                try:
                    output = conversational_chat(user_input, chain)
                except Exception as e:
                    output = f"Sorry, an error occurred: {e}"

                # Update chat history
                st.session_state["history"].append({"user": user_input, "bot": output})

    # Display conversation history
    with response_container:
        if st.session_state["history"]:
            for i, chat in enumerate(st.session_state["history"]):
                # Use fun emojis for user and bot
                message(chat["user"], is_user=True, key=f"user_{i}", avatar_style="big-smile") 
                message(chat["bot"], key=f"bot_{i}", avatar_style="fun-emoji")  

# Run main
if __name__ == "__main__":
    main()

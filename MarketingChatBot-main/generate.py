import openai
from config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE

openai.api_key = OPENAI_API_KEY

def generate_response_from_api(user_input):
    """
    Generate response using OpenAI API for general questions.
    """
    try:
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a marketing insight assistant."},
                {"role": "user", "content": user_input}
            ],
            temperature=TEMPERATURE
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Maaf, terjadi kesalahan saat menghubungi API OpenAI: {e}"
    
def generate_response(user_input, dataset_response=None):
    """
    Generate chatbot response.
    - If dataset_response exists, return it.
    - Otherwise, fallback to OpenAI API.
    """
    if dataset_response:  # Dataset has an answer
        return dataset_response
    else:  # Fallback to OpenAI API
        return generate_response_from_api(user_input)

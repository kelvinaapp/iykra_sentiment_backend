from langchain.prompts import PromptTemplate

# System Prompt
def get_system_prompt():
    """
    Returns the system prompt to define the chatbot's behavior.
    """
    return PromptTemplate(template="""
You are an advanced marketing assistant, providing data-driven insights and actionable recommendations to improve product marketing strategies. 
If the requested data is not available in the dataset, provide a thoughtful and general response based on your knowledge as an AI assistant.
""")

# Task-Specific Prompts
def get_task_prompt(question_type):
    """
    Returns task-specific prompts based on the question type.
    """
    task_prompts = {
        "real_time_insights": """
How do you provide real-time insights using TrendAnalyzer? 
Answer by explaining how the tool monitors current market trends, collects relevant data, and transforms it into actionable insights for strategic decision-making.
Provide examples related to specific products or industries.
""",
        "analyze_audience": """
How do you analyze target audiences effectively with AudienceProfiler? 
Explain the methods and data sources used by AudienceProfiler, such as demographic analysis, psychographic profiling, and behavioral data.
Provide recommendations on how to adjust campaigns based on audience profiles.
""",
        "campaign_optimizer": """
How does CampaignOptimizer improve marketing campaign performance? 
Elaborate on its ability to evaluate past campaigns, identify key success factors, and optimize resource allocation for future initiatives.
Suggest specific types of campaigns (e.g., social media, influencer collaborations) for different product categories.
""",
        # Add other task-specific prompts as necessary
    }
    return task_prompts.get(question_type, """
Maaf, jenis pertanyaan yang diminta tidak dikenali. Namun, berikut adalah wawasan umum:
- Untuk pemasaran berbasis data, penting untuk memahami audiens melalui analisis demografis dan perilaku.
- Tren pasar terkini sering kali melibatkan strategi digital, seperti memanfaatkan platform media sosial dan kampanye berbasis AI.
Silakan sesuaikan pertanyaan untuk jawaban yang lebih spesifik.
""")

def handle_unknown_responses(question, is_data_missing=False):
    """
    Handles cases where the answer is unknown or data is missing, providing general insights.
    """
    general_insight = {
        "default": (
            "Sebagai asisten pemasaran AI, saya merekomendasikan untuk fokus pada strategi berikut: "
            "1. Analisis tren pasar terkini untuk mengetahui kebutuhan audiens. "
            "2. Optimalkan kampanye dengan menggunakan data perilaku pelanggan. "
            "3. Gunakan media sosial dan kolaborasi dengan influencer untuk menjangkau audiens baru."
        ),
        "dataset_missing": (
            "Maaf, data spesifik tentang permintaan Anda tidak tersedia dalam dataset. "
            "Namun, secara umum, strategi pemasaran yang efektif melibatkan: "
            "1. Pemahaman audiens melalui survei dan wawasan demografis. "
            "2. Mengidentifikasi USP (Unique Selling Proposition) produk Anda. "
            "3. Menggunakan pemasaran omnichannel untuk menjangkau pelanggan secara maksimal."
        )
    }

    if is_data_missing:
        return general_insight["dataset_missing"]
    
    return general_insight["default"]

# Example Usage
if __name__ == "__main__":
    # Example: Retrieve system prompt
    system_prompt = get_system_prompt()
    print(system_prompt.template)

    # Example: Retrieve task-specific prompt
    task_prompt = get_task_prompt("recommend_campaign")
    print(task_prompt)

    # Example: Handle unknown response
    bot_response = "I don't know"  # Example response from the bot
    adjusted_response = handle_unknown_responses(bot_response)
    print(adjusted_response)

    # Example: Handle missing data in dataset
    general_response = handle_unknown_responses(
        "Strategi pemasaran meliputi analisis audiens, tren pasar, dan rekomendasi kampanye kreatif.", 
        is_data_missing=True
    )
    print(general_response)

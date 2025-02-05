from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain.agents.agent_toolkits import create_retriever_tool
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
import os
from db.database import DATABASE_URL
import asyncio
from tools.faiss_vectordb import load_vector_db

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str
    
class QueryOutput(TypedDict):
    """Generated SQL query."""
    query: Annotated[str, ..., "Syntactically valid SQL query."]

class LangChainRAG:
    def __init__(self, vector_store_path="vector_db", model_name="gpt-4o-mini", temperature=0, streaming=True):
        """
        Initialize LangChainRAG with configuration
        
        Args:
            vector_store_path (str): Path to vector store
            model_name (str): Name of the OpenAI model to use
            temperature (float): Temperature for model generation
            streaming (bool): Whether to use streaming for model generation
        """
        load_dotenv()
        self.memory = MemorySaver()
        self.config = {"configurable": {"thread_id": "abc123"}}
        
        # Set environment variables
        if not os.environ.get("LANGSMITH_API_KEY"):
            os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
            os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING")
        
        # Initialize components
        self.db = SQLDatabase.from_uri(DATABASE_URL)
        self.llm = ChatOpenAI(model=model_name, temperature=temperature, streaming=streaming)
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = self.toolkit.get_tools()
        
        # Initialize vector store
        if os.path.exists(vector_store_path):
            self.vector_store = load_vector_db(vector_store_path)
            self.setup_retriever()
        
        # Setup agent
        self.setup_agent()
    
    def setup_retriever(self):
        """Setup vector store retriever and create retriever tool"""
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        description = (
            "Use to look up values to filter on. Input is an approximate spelling "
            "of the proper noun, output is valid proper nouns. Use the noun most "
            "similar to the search."
        )
        
        self.retriever_tool = create_retriever_tool(
            self.retriever,
            name="search_proper_nouns",
            description=description,
        )
        self.tools.append(self.retriever_tool)
    
    def setup_agent(self):
        """Setup the agent with system message and tools"""
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
            You are an agent designed to interact with a SQL database.
            Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
            Unless the user specifies a specific number of examples they wish to obtain, LIMIT your query to at most {top_k} results.
            You can order the results by a relevant column to return the most interesting examples in the database.
            Never query for all the columns from a specific table, only ask for the relevant columns given the question.
            You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

            DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

            To start you should ALWAYS look at the tables in the database to see what you can query.
            Do NOT skip this step. Only use the following tables:
            {table_info}
            
            Pay attention to use only the column names that you can see in the table schema. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
            FOCUS only on insight that can be generated from the database. DO NOT answer questions that is not related to the database.
            ONCE AGAIN, DO NOT ANSWER QUESTIONS THAT ARE NOT RELATED TO THE DATABASE.
            
            You have access to tools for interacting with the database.
            Only use the below tools. Only use the information returned by the below tools to construct your final answer.
            
            Guidlines for the query:
                - if the question asks for statisctical calculation, ALWAYS use statistical functions (AVG, SUM, MIN, MAX, etc.)
                - ALWAYS LIMIT your query to at most {top_k}
                - if the question ask for sentiment, you can join social_media with sentiment_social_media
            
            Guidelines for the response:
                - Use Rupiah Currency
                - Always maintain a professional and helpful tone.
                - Format your response in a clear and structured way
                - Never give explanation without supporting data from the database.
            """)
        ])

        system_message = prompt_template.format(
            dialect=self.db.dialect,
            table_info=self.db.get_table_info(),
            top_k=50
        )
        
        suffix = (
            "If you need to filter on a proper noun like a product name, brand, category, sentiment, or other entity, you must ALWAYS first look up "
            "the filter value using the 'search_proper_nouns' tool! Do not try to "
            "guess at the proper name - use this function to find similar ones."
        )
        
        system = f"{system_message}\n\n{suffix}"
        self.agent = create_react_agent(self.llm, self.tools, prompt=system, checkpointer=self.memory)

    async def process_event(self, event):
        """Process streaming events from the agent"""
        try:
            kind = event["event"]
            tool_name = event['name']
            
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    print(content, end="")
            elif kind == "on_tool_start":
                if tool_name == "search_proper_nouns":
                    print("Vector DB Tools: Searching...")
                elif tool_name == "sql_db_query_checker":
                    print("Query Checker Tools: Checking SQL Query...")
                elif tool_name == "sql_db_query":
                    print("Query Executor Tools: Creating SQL Query...")
                print(f"\nStarting tool: {tool_name} with inputs: {event['data'].get('input')}")
            elif kind == "on_tool_end":
                if tool_name == "search_proper_nouns":
                    print("Vector DB Tools: Vector DB Searched")
                elif tool_name == "sql_db_query_checker":
                    print("Query Checker Tools: Query Checked")
                elif tool_name == "sql_db_query":
                    print("Query Executor Tools: Query Executed")
        except Exception as e:
            print(f"Error processing event: {e}")

    async def run_agent(self, question: str):
        """
        Run the agent with a given question
        
        Args:
            question (str): Question to ask the agent
        """
        async for event in self.agent.astream_events(
            {"messages": [HumanMessage(content=question)]},
            version="v2",
            config=self.config,
        ):
            await self.process_event(event)

# Example usage
if __name__ == "__main__":
    # Initialize the RAG system
    rag = LangChainRAG()
    
    # Example questions
    questions = [
        "Jelaskan trend penjualan Adidas di 2024 setiap Quartilnya",
        # "Berapa penjualanku di Q4 2024"
    ]
    
    # Run questions
    for question in questions:
        asyncio.run(rag.run_agent(question))
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
import uuid
import logging
import json

# Set logging level for all loggers
logging.getLogger("langchain").setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str
    
class QueryOutput(TypedDict):
    """Generated SQL query."""
    query: Annotated[str, ..., "Syntactically valid SQL query."]

class LangChainRAG:
    def __init__(self, vector_store=None, model_name="gpt-4o-mini", temperature=0, streaming=True):
        """
        Initialize LangChainRAG with configuration
        
        Args:
            vector_store: Pre-loaded vector store instance
            model_name (str): Name of the OpenAI model to use
            temperature (float): Temperature for model generation
            streaming (bool): Whether to use streaming for model generation
        """
        load_dotenv()
        self.memory = MemorySaver()
        self.config = {"configurable": {"thread_id": self.generate_thread_id()}}
        
        # Set environment variables
        if not os.environ.get("LANGSMITH_API_KEY"):
            os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
            os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING")
        
        # Initialize components
        self.db = SQLDatabase.from_uri(DATABASE_URL)
        self.llm = ChatOpenAI(model=model_name, temperature=temperature, streaming=streaming)
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = self.toolkit.get_tools()
        
        # Set vector store and setup retriever if provided
        self.vector_store = vector_store
        if vector_store:
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
                    - if the question asks about trends, ALWAYS answer in AVERAGE unless explicitly asked otherwise.
                        let say if the question ask about one month, calculate in daily/weekly average,
                        if the question ask about one week, calculate in daily average,
                        if the question ask about Quartile, calculate in Weekly average,
                        if the question ask about Yearly, calculate in Monthly average.
                        etc.
                    - Use a nested list if it needs to.
                
                Guidelines for the response:
                    - Use Rupiah Currency
                    - Always maintain a professional and helpful tone.
                    - Format your response in a clear and structured way
                    - NEVER give explanation without supporting data from the database.
                    - Unless explicitly asked in the question, NEVER answer in table format 
                    - NEVER SHOW a SQL Query
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

    async def run_agent(self, question: str):
        """Run the agent with streaming events"""
        try:
            current_token = ""
            async for event in self.agent.astream_events(
                {"messages": [HumanMessage(content=question)]},
                version="v2",
                config=self.config,
            ):
                async for processed_event in self.process_event(event):
                    if processed_event:  # Only yield non-empty events
                        # Accumulate tokens and send when we have a complete word
                        current_token += processed_event
                        if current_token.endswith(" ") or any(current_token.endswith(p) for p in [".", ",", "!", "?", ":", ";"]):
                            # Format the event as a proper SSE data event
                            yield json.dumps({"text": current_token})
                            current_token = ""
            
            # Send any remaining token
            if current_token:
                yield json.dumps({"text": current_token})
        except Exception as e:
            error_msg = json.dumps({"error": str(e)})
            yield error_msg
            logger.error(f"Error in run_agent: {str(e)}")

    async def process_event(self, event):
        """Process streaming events from the agent"""
        try:
            kind = event["event"]
            
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                # Handle AIMessageChunk directly
                if hasattr(chunk, "content"):
                    content = chunk.content
                    if content:
                        yield content
        except Exception as e:
            error_msg = f"Error processing event: {str(e)}"
            logger.error(f"Error processing event: {str(e)}, Event: {event}")
            yield error_msg

    def generate_thread_id(self):
        """Generate a unique thread ID"""
        return str(uuid.uuid4())


# # Example usage
# if __name__ == "__main__":
#     # Initialize the RAG system
#     rag = LangChainRAG()
    
#     # Example questions
#     questions = [
#         "Ada brand apa saja di database?",
#         # "Berapa penjualanku di Q4 2024"
#     ]
    
#     # Run questions
#     async def response():
#         for question in questions:
#             async for event in rag.run_agent(question):
#                 print(event, end="")

#     asyncio.run(response())
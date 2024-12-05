import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA
import json
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def prepare_documents(inventory_data):
    """Prepare documents for RAG from inventory data."""
    return [
        f"SKU: {item['skuId']}\nName: {item['skuName']}\n"
        f"Description: {item['description']}\nStock: {item['stock']}"
        for item in inventory_data['inventory']
    ]

def initialize_rag(inventory_path: str):
    """Initialize RAG system using inventory data from file."""
    # Read the inventory data
    with open(inventory_path, 'r') as f:
        inventory_data = json.load(f)
    
    # Create documents
    documents = prepare_documents(inventory_data)
    
    # Initialize embedding model and vector store
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(documents, embeddings)
    
    # Initialize language model
    llm = OpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY)
    
    # Create and return QA chain
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )

def query_inventory(qa_chain, question: str) -> str:
    """Query the RAG system."""
    return qa_chain.run(question)

# Initialize the system with existing inventory file
inventory_path = "Rag/data/inventory.json"
qa_system = initialize_rag(inventory_path)

# Example query
result = query_inventory(qa_system, "What wheat flour options do we have?")
print(result)
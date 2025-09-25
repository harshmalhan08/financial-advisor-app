# main.py
import os
import uuid
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Dict


from dotenv import load_dotenv
load_dotenv()


from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondenseQuestionChatEngine



class NewChatRequest(BaseModel):
    pass

class NewChatResponse(BaseModel):
    chat_id: str
    message: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    chat_id: str


chat_engines: Dict[str, CondenseQuestionChatEngine] = {}
llama_index_instance = None

# --- Application

@asynccontextmanager
async def lifespan(app: FastAPI):
    #  START
    print("--- Server starting up... ---")

    # .env file
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable not set. Please check your .env file.")

    print("Configuring LLM and embedding models...")
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    Settings.llm = Gemini(model="models/gemini-1.5-flash-latest")

    knowledge_dir = "knowledge_base"
    if not os.path.exists(knowledge_dir) or not os.listdir(knowledge_dir):
        print(f"Warning: The '{knowledge_dir}' directory is empty or does not exist.")
        os.makedirs(knowledge_dir, exist_ok=True)
        with open(os.path.join(knowledge_dir, "placeholder.txt"), "w") as f:
            f.write("This is a placeholder file. Add your financial knowledge here.")

    print(f"Loading documents from '{knowledge_dir}'...")
    reader = SimpleDirectoryReader(knowledge_dir)
    documents = reader.load_data()

    print("Creating the vector store index... (This may take a moment)")
    global llama_index_instance
    llama_index_instance = VectorStoreIndex.from_documents(documents)
    print("--- Index created successfully. Server is ready. ---")

    yield

    # Close app
    print("--- Server shutting down... ---")
    chat_engines.clear()


# FastAPI App
app = FastAPI(lifespan=lifespan)


# Dependency
async def get_index():
    if llama_index_instance is None:
        raise HTTPException(status_code=503, detail="Index is not initialized.")
    return llama_index_instance


#API Endpoints

@app.post("/chat/new", response_model=NewChatResponse)
async def create_new_chat(index: VectorStoreIndex = Depends(get_index)):
    chat_id = str(uuid.uuid4())
    memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

    chat_engine = index.as_chat_engine(
        chat_mode="condense_question",
        memory=memory,
        # system_prompt
        verbose=True
    )

    chat_engines[chat_id] = chat_engine

    return NewChatResponse(
        chat_id=chat_id,
        message="New chat session created successfully."
    )


@app.post("/chat/{chat_id}", response_model=ChatResponse)
async def chat_with_advisor(chat_id: str, request: ChatRequest):
    if chat_id not in chat_engines:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    chat_engine = chat_engines[chat_id]
    response = await chat_engine.achat(request.message)
    response_text = str(response)

    return ChatResponse(response=response_text, chat_id=chat_id)

@app.get("/")
async def root():
    return {"message": "Welcome to the Financial Advisor API. Visit /docs for the interactive API documentation."}
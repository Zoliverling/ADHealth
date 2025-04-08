from typing import List, Dict, Any
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv

load_dotenv()

class KnowledgeBaseProcessor:
    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = knowledge_base_path
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.vector_store = None

    def load_documents(self) -> List[Dict[str, Any]]:
        """Load documents from the knowledge base directory."""
        loader = DirectoryLoader(
            self.knowledge_base_path,
            glob="**/*.txt",
            loader_cls=TextLoader
        )
        documents = loader.load()
        return self.text_splitter.split_documents(documents)

    def initialize_vector_store(self):
        """Initialize or load the vector store with documents."""
        documents = self.load_documents()
        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=os.path.join(self.knowledge_base_path, "chroma_db")
        )
        self.vector_store.persist()

    def query_knowledge_base(self, query: str, k: int = 3) -> List[str]:
        """Query the knowledge base and return relevant documents."""
        if not self.vector_store:
            self.initialize_vector_store()
        
        docs = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

    def query_knowledge_base_with_scores(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Query the knowledge base and return relevant documents with similarity scores."""
        if not self.vector_store:
            self.initialize_vector_store()
        
        # Get documents with scores
        docs_and_scores = self.vector_store.similarity_search_with_score(query, k=k)
        
        # Format results
        results = []
        for doc, score in docs_and_scores:
            # Normalize score to 0-1 range (higher is better)
            normalized_score = 1.0 - (score / 2.0)  # Assuming scores are typically 0-2 range
            normalized_score = max(0.0, min(1.0, normalized_score))  # Clamp to 0-1
            
            # Extract source if available
            source = doc.metadata.get('source', 'Unknown source')
            title = doc.metadata.get('title', 'Untitled')
            
            results.append({
                'content': doc.page_content,
                'score': normalized_score,
                'source': source,
                'title': title
            })
        
        return results

    def add_document(self, content: str, source: str):
        """Add a new document to the knowledge base."""
        docs = self.text_splitter.split_text(content)
        if not self.vector_store:
            self.initialize_vector_store()
        
        self.vector_store.add_texts(
            texts=docs,
            metadatas=[{"source": source} for _ in docs]
        )
        self.vector_store.persist()
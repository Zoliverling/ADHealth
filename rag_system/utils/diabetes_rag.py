from .knowledge_base_processor import KnowledgeBaseProcessor
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

class DiabetesRAGSystem:
    def __init__(self, knowledge_base_path):
        self.kb_processor = KnowledgeBaseProcessor(knowledge_base_path)
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
        
        # Initialize knowledge base
        self.kb_processor.initialize_vector_store()
        
        # Create prompt template for generating insights
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a medical expert. Provide one clear action or key alert in 5-8 words. Start with an action verb when possible:

{context}"""),
            ("human", "{query}")
        ])
        
        # Create the chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
    
    def generate_insight(self, query: str) -> str:
        """
        Generate an insight based on the query using RAG
        """
        relevant_docs = self.kb_processor.query_knowledge_base(query, k=1)
        context = relevant_docs[0] if relevant_docs else ""
        
        response = self.chain.run(context=context, query=query)
        return response.strip()
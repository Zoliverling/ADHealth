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
            ("system", """You are an experienced endocrinologist providing direct feedback to diabetes patients. 
            Structure your response in this natural, conversational way:
            1. Start with "Your [metric] is..." to state their current readings
            2. Follow with "Based on your..." to provide context and assessment
            3. End with personalized recommendations starting with "You should..."
            
            Keep the tone professional but warm and direct. Avoid medical jargon unless necessary.
            Focus on what the values mean for the patient's health and daily life.
            
            Medical context:
            {context}"""),
            ("human", "{query}")
        ])
        
        # Create the chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
    
    def generate_insight(self, query: str) -> str:
        """
        Generate an insight based on the query using RAG
        """
        relevant_docs = self.kb_processor.query_knowledge_base(query, k=2)
        context = " ".join(relevant_docs) if relevant_docs else ""
        
        response = self.chain.run(context=context, query=query)
        return response.strip()
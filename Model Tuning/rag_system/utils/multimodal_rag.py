from .knowledge_base_processor import KnowledgeBaseProcessor
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import base64
import os
from PIL import Image
import io

class MultimodalRAGSystem:
    def __init__(self, knowledge_base_path):
        self.kb_processor = KnowledgeBaseProcessor(knowledge_base_path)
        # Using GPT-4 Vision for multimodal capabilities
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1, max_tokens=1000)
        # Fallback to GPT-3.5 Turbo for text-only queries to optimize cost
        self.text_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
        
        # Initialize knowledge base
        self.kb_processor.initialize_vector_store()
        
        # Create prompt template for text-only insights
        self.text_prompt_template = ChatPromptTemplate.from_messages([
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
        
        # Create prompt template for multimodal insights with image
        self.multimodal_prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an experienced endocrinologist providing direct feedback to diabetes patients.
            You have been given a diabetes-related image and a query. The image may be of:
            - A glucose meter or continuous glucose monitor reading
            - A food plate for carb estimation
            - An insulin injection/pump site
            - A medical document or chart related to diabetes
            
            Analyze both the image and the query to provide accurate insights.
            Structure your response in this natural, conversational way:
            1. Start with "Your [metric/image shows] is..." to acknowledge what you see
            2. Follow with "Based on your..." to provide context and assessment
            3. End with personalized recommendations starting with "You should..."
            
            Keep the tone professional but warm and direct. Avoid medical jargon unless necessary.
            Focus on what the information means for the patient's health and daily life.
            
            Medical context:
            {context}"""),
            ("human", "{query}"),
            ("human", [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "{image_url}",
                        "detail": "high"
                    }
                }
            ])
        ])
        
        # Create the chains
        self.text_chain = LLMChain(llm=self.text_llm, prompt=self.text_prompt_template)
        self.multimodal_chain = LLMChain(llm=self.llm, prompt=self.multimodal_prompt_template)
    
    def _encode_image_as_base64(self, image_path):
        """
        Encode the image at the given path as a base64 string.
        Returns a data URL for the image.
        """
        if not image_path or not os.path.exists(image_path):
            return None
            
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        # Create a data URL
        image_type = image_path.split('.')[-1].lower()
        if image_type not in ['jpg', 'jpeg', 'png']:
            image_type = 'jpeg'  # default
            
        return f"data:image/{image_type};base64,{encoded_string}"
    
    def generate_insight(self, query: str, image_path=None) -> dict:
        """
        Generate an insight based on the query and optional image using RAG
        Returns a dictionary with the response, retrieved documents, and confidence scores
        """
        # Get relevant documents from knowledge base with scores
        results = self.kb_processor.query_knowledge_base_with_scores(query, k=3)
        relevant_docs = [doc['content'] for doc in results]
        context = " ".join(relevant_docs) if relevant_docs else ""
        
        # Choose the appropriate chain based on whether an image is provided
        if image_path and os.path.exists(image_path):
            try:
                # Encode image for API
                image_url = self._encode_image_as_base64(image_path)
                
                # Use multimodal chain with image
                response = self.multimodal_chain.run(
                    context=context,
                    query=query,
                    image_url=image_url
                )
            except Exception as e:
                # Log the error and fall back to text-only chain
                print(f"Error processing image: {str(e)}")
                response = self.text_chain.run(
                    context=context,
                    query=query
                )
        else:
            # Use text-only chain (more cost-effective)
            response = self.text_chain.run(
                context=context,
                query=query
            )
        
        # Calculate overall confidence based on document scores
        confidence = 0
        if results:
            confidence = sum(doc['score'] for doc in results) / len(results)
        
        return {
            'response': response.strip(),
            'retrieved_docs': results,
            'confidence': confidence
        } 
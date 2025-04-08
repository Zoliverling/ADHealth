from .multimodal_rag import MultimodalRAGSystem
import os
import re
import base64

class DiabetesMultimodalInterface:
    def __init__(self):
        knowledge_base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'knowledge_base')
        self.rag_system = MultimodalRAGSystem(knowledge_base_path)
    
    def _normalize_text(self, text):
        """Normalize text by removing special characters and extra whitespace"""
        # Remove special characters except periods and commas
        text = re.sub(r'[^\w\s.,]', '', text)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Add proper spacing after periods and commas
        text = re.sub(r'\.(?! )', '. ', text)
        text = re.sub(r',(?! )', ', ', text)
        return text.strip()
    
    def _format_insight(self, text):
        """Format insight into clear, professional medical statements"""
        # Split into sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        # Format each sentence as a professional statement
        formatted_sentences = []
        for sentence in sentences:
            if sentence:
                # Remove any leading numbers or bullets
                clean_sentence = re.sub(r'^\d+\.|^\*|\-', '', sentence).strip()
                # Capitalize first letter
                if clean_sentence:
                    formatted_sentences.append(f"{clean_sentence.capitalize()}")
        
        # Join sentences with proper spacing
        return '. '.join(formatted_sentences) + '.'

    def _prepare_image_for_analysis(self, image_path):
        """Prepare image for analysis if provided"""
        if not image_path or not os.path.exists(image_path):
            return None
        
        # Return the path for the multimodal RAG system to process
        return image_path

    def get_insights(self, metrics, image_path=None):
        """
        Generate personalized medical insights based on provided clinical metrics using the RAG system.
        Now supporting image analysis for additional context.
        """
        insights = {}
        
        # Prepare image for analysis if provided
        prepared_image = self._prepare_image_for_analysis(image_path)
        
        # Create context strings with patient-focused terminology
        glucose_context = f"your blood glucose is {metrics.get('glucose_level')} mg/dL" if metrics.get('glucose_level') is not None else None
        insulin_context = f"your insulin dose is {metrics.get('insulin_units')} units" if metrics.get('insulin_units') is not None else None
        bp_context = (f"your blood pressure is {metrics.get('systolic_bp')}/{metrics.get('diastolic_bp')} mmHg" 
                     if metrics.get('systolic_bp') is not None and metrics.get('diastolic_bp') is not None else None)
        
        # Generate personalized glucose assessment
        if metrics.get('glucose_level') is not None:
            level = metrics['glucose_level']
            context_parts = []
            if glucose_context: context_parts.append(glucose_context)
            if insulin_context: context_parts.append(insulin_context)
            if bp_context: context_parts.append(bp_context)
            
            context = " and ".join(context_parts)
            
            if level > 180:
                query = f"The patient's measurements show that {context}. Please provide a personalized assessment for their high blood glucose, considering these values and potential risks."
            elif level < 70:
                query = f"The patient's measurements show that {context}. Please provide a personalized assessment for their low blood glucose, considering these values and immediate needs."
            else:
                query = f"The patient's measurements show that {context}. Please provide a personalized assessment of their glucose control and what this means for their health."
            
            try:
                result = self.rag_system.generate_insight(query, prepared_image)
                normalized_insight = self._normalize_text(result['response'])
                insights['glucose'] = normalized_insight
                insights['glucose_sources'] = result.get('retrieved_docs', [])
                insights['glucose_confidence'] = result.get('confidence', 0)
            except Exception as e:
                print(f"Error generating glucose insight: {str(e)}")
                insights['glucose'] = "Unable to generate insight at this time."
                insights['glucose_sources'] = []
                insights['glucose_confidence'] = 0
        
        # Generate personalized insulin assessment
        if metrics.get('insulin_units') is not None:
            context_parts = []
            if insulin_context: context_parts.append(insulin_context)
            if glucose_context: context_parts.append(glucose_context)
            if bp_context: context_parts.append(bp_context)
            
            context = " and ".join(context_parts)
            query = f"The patient's measurements show that {context}. Please provide a personalized assessment of their insulin therapy and its effectiveness."
            
            try:
                result = self.rag_system.generate_insight(query, prepared_image)
                normalized_insight = self._normalize_text(result['response'])
                insights['insulin'] = normalized_insight
                insights['insulin_sources'] = result.get('retrieved_docs', [])
                insights['insulin_confidence'] = result.get('confidence', 0)
            except Exception as e:
                print(f"Error generating insulin insight: {str(e)}")
                insights['insulin'] = "Unable to generate insight at this time."
                insights['insulin_sources'] = []
                insights['insulin_confidence'] = 0
        
        # Generate personalized blood pressure assessment
        if metrics.get('systolic_bp') is not None and metrics.get('diastolic_bp') is not None:
            sys, dia = metrics['systolic_bp'], metrics['diastolic_bp']
            context_parts = []
            if bp_context: context_parts.append(bp_context)
            if glucose_context: context_parts.append(glucose_context)
            if insulin_context: context_parts.append(insulin_context)
            
            context = " and ".join(context_parts)
            
            if sys >= 180 or dia >= 120:
                query = f"The patient's measurements show that {context}. Please provide a personalized urgent assessment of their critical blood pressure situation."
            else:
                query = f"The patient's measurements show that {context}. Please provide a personalized assessment of their blood pressure control."
            
            try:
                result = self.rag_system.generate_insight(query, prepared_image)
                normalized_insight = self._normalize_text(result['response'])
                insights['blood_pressure'] = normalized_insight
                insights['bp_sources'] = result.get('retrieved_docs', [])
                insights['bp_confidence'] = result.get('confidence', 0)
            except Exception as e:
                print(f"Error generating blood pressure insight: {str(e)}")
                insights['blood_pressure'] = "Unable to generate insight at this time."
                insights['bp_sources'] = []
                insights['bp_confidence'] = 0
        
        return insights

    def get_chat_response(self, message, entries_context, image_path=None):
        """
        Generate a response to a user's chat message using the RAG system, now with image support.
        
        Args:
            message (str): The user's chat message
            entries_context (list): List of recent entries with their data
            image_path (str): Optional path to an uploaded image
        """
        # Prepare image for analysis if provided
        prepared_image = self._prepare_image_for_analysis(image_path)
        
        # Format the context for the RAG system
        context = "Recent health data:\n"
        for entry in entries_context:
            context += f"Date: {entry['date']}\n"
            if entry['glucose'] is not None:
                context += f"Glucose: {entry['glucose']} mg/dL\n"
            if entry['insulin'] is not None:
                context += f"Insulin: {entry['insulin']} units\n"
            if entry['bp'] is not None:
                context += f"Blood Pressure: {entry['bp']}\n"
            if entry.get('carbs') is not None:
                context += f"Carbs: {entry['carbs']}g\n"
            context += "\n"
        
        # Create a query combining the user's message and context
        query = f"User Question: {message}\n\nContext:\n{context}\n\nBased on the user's health data and question, provide a helpful response that addresses their query and incorporates relevant information from their recent measurements when applicable."
        
        try:
            # Generate and format the response with the image if provided
            result = self.rag_system.generate_insight(query, prepared_image)
            return {
                'response': self._format_insight(result['response']),
                'sources': result.get('retrieved_docs', []),
                'confidence': result.get('confidence', 0)
            }
        except Exception as e:
            # Log the error and return a fallback response
            print(f"Error generating chat response: {str(e)}")
            return {
                'response': "I'm sorry, I encountered an error processing your request. Please try again or rephrase your question.",
                'sources': [],
                'confidence': 0
            } 
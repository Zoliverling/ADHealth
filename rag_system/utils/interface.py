from .diabetes_rag import DiabetesRAGSystem
import os
import re

class DiabetesInsightInterface:
    def __init__(self):
        knowledge_base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'knowledge_base')
        self.rag_system = DiabetesRAGSystem(knowledge_base_path)
    
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

    def get_insights(self, metrics):
        """
        Generate personalized medical insights based on provided clinical metrics using the RAG system.
        """
        insights = {}
        
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
            
            raw_insight = self.rag_system.generate_insight(query)
            normalized_insight = self._normalize_text(raw_insight)
            insights['glucose'] = normalized_insight
        
        # Generate personalized insulin assessment
        if metrics.get('insulin_units') is not None:
            context_parts = []
            if insulin_context: context_parts.append(insulin_context)
            if glucose_context: context_parts.append(glucose_context)
            if bp_context: context_parts.append(bp_context)
            
            context = " and ".join(context_parts)
            query = f"The patient's measurements show that {context}. Please provide a personalized assessment of their insulin therapy and its effectiveness."
            raw_insight = self.rag_system.generate_insight(query)
            normalized_insight = self._normalize_text(raw_insight)
            insights['insulin'] = normalized_insight
        
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
            
            raw_insight = self.rag_system.generate_insight(query)
            normalized_insight = self._normalize_text(raw_insight)
            insights['blood_pressure'] = normalized_insight
        
        return insights
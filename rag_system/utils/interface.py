from .diabetes_rag import DiabetesRAGSystem
import os

class DiabetesInsightInterface:
    def __init__(self):
        knowledge_base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'knowledge_base')
        self.rag_system = DiabetesRAGSystem(knowledge_base_path)
    
    def get_insights(self, metrics):
        """
        Generate insights based on provided metrics using the RAG system
        """
        insights = {}
        
        # Get glucose insights
        if metrics.get('glucose_level') is not None:
            level = metrics['glucose_level']
            if level > 180:
                query = f"Immediate action for {level} mg/dL high glucose?"
            elif level < 70:
                query = f"Immediate action for {level} mg/dL low glucose?"
            else:
                query = f"Status assessment for {level} mg/dL glucose?"
            insights['glucose'] = self.rag_system.generate_insight(query)
        
        # Get insulin insights
        if metrics.get('insulin_units') is not None:
            glucose = metrics.get('glucose_level', 'unknown')
            query = f"Key safety alert for {metrics['insulin_units']} units at {glucose} mg/dL?"
            insights['insulin'] = self.rag_system.generate_insight(query)
        
        # Get blood pressure insights
        if metrics.get('systolic_bp') is not None and metrics.get('diastolic_bp') is not None:
            sys, dia = metrics['systolic_bp'], metrics['diastolic_bp']
            if sys >= 180 or dia >= 120:
                query = "Emergency action for critical blood pressure?"
            else:
                query = f"Key alert for {sys}/{dia} mmHg blood pressure?"
            insights['blood_pressure'] = self.rag_system.generate_insight(query)
        
        return insights
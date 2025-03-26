from typing import List
from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader
import json

__all__ = ['JSONKnowledgeBaseLoader']

class JSONKnowledgeBaseLoader(BaseLoader):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        with open(self.file_path, 'r') as file:
            data = json.load(file)
            documents = []
            
            for item in data:
                content = item.get('content', '')
                if not content:
                    continue
                    
                metadata = {
                    'source': item.get('source', ''),
                    'title': item.get('title', ''),
                    'type': item.get('type', ''),
                    'confidence': item.get('confidence', 1.0),
                    'topics': item.get('topics', [])
                }
                
                if 'publication_info' in item:
                    metadata.update(item['publication_info'])
                    
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                documents.append(doc)
                
        return documents

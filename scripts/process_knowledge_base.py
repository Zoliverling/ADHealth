import json
import os
from typing import Dict, List, Any
import re
import logging
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ContentProcessor(ABC):
    @abstractmethod
    def process_article(self, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

class ADAContentProcessor(ContentProcessor):
    def process_article(self, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        chunks = []
        content = article.get('content', '')
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
        
        for para in paragraphs:
            chunks.append({
                "content": para,
                "type": "community",
                "confidence": 0.9,
                "source": article.get('url', ''),
                "title": article.get('title', 'Untitled'),
                "topics": [h.lower() for h in article.get('headings', []) if h and h != "Navigation"],
                "bullet_points": [b for b in article.get('bullet_points', []) if b]
            })
        return chunks

class PubMedContentProcessor(ContentProcessor):
    def process_article(self, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        chunks = []
        abstract = article.get('abstract', '')
        content = article.get('content', '')
        
        if abstract:
            chunks.append({
                "content": abstract,
                "type": "academic_abstract",
                "confidence": 0.95,
                "source": article.get('pubmed_link', ''),
                "title": article.get('title', 'Untitled'),
                "topics": ["abstract"] + article.get('keywords', []),
                "publication_info": {
                    "authors": article.get('authors', []),
                    "journal": article.get('journal', ''),
                    "year": article.get('publication_date', '')
                }
            })
        
        if content:
            sections = content.split('\n\n')
            for section in sections:
                if len(section.strip()) > 50:
                    chunks.append({
                        "content": section.strip(),
                        "type": "academic_content",
                        "confidence": 0.93,
                        "source": article.get('url', ''),
                        "title": article.get('title', 'Untitled'),
                        "topics": article.get('keywords', []),
                        "publication_info": {
                            "authors": article.get('authors', []),
                            "journal": article.get('journal', ''),
                            "year": article.get('year', '')
                        }
                    })
        return chunks

class TextContentProcessor(ContentProcessor):
    def process_article(self, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        chunks = []
        content = article.get('content', '')
        sections = [s.strip() for s in content.split('\n\n') if len(s.strip()) > 50]
        
        for section in sections:
            chunks.append({
                "content": section,
                "type": "text_content",
                "confidence": 0.85,
                "source": article.get('filename', 'Unknown'),
                "title": article.get('title', 'Text Document'),
                "topics": article.get('topics', ["general"]),
            })
        return chunks

class KnowledgeBaseProcessor:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processors = {
            'community': ADAContentProcessor(),
            'academic': PubMedContentProcessor(),
            'text': TextContentProcessor()
        }
    
    def detect_content_type(self, filename: str, data: Any) -> str:
        if filename.endswith('.txt'):
            return 'text'
        if 'pubmed' in filename.lower():
            return 'academic'
        return 'community'
    
    def clean_content(self, content: str) -> str:
        patterns_to_remove = [
            r'\d{4}\s+Crystal\s+Drive.+?Copyright.+?reserved\.',
            r'Learn your risk for type 2 and take steps to prevent it',
            r'With your support, the American Diabetes Association',
            r'Disclaimer:.*?(?=\n|$)',
            r'Copyright ©.*?(?=\n|$)'
        ]
        
        cleaned = content
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
        
        return cleaned.strip()

    def process_file(self, filename: str) -> List[Dict[str, Any]]:
        logging.info(f"Processing file: {filename}")
        
        file_path = os.path.join(self.input_dir, filename)
        
        if filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                data = [{
                    'content': content,
                    'filename': filename,
                    'title': os.path.splitext(filename)[0],
                    'topics': ['text_content']
                }]
        else:
            with open(file_path, 'r') as f:
                data = json.load(f)
        
        content_type = self.detect_content_type(filename, data)
        processor = self.processors[content_type]
        
        knowledge_base = []
        total_articles = len(data)
        
        for idx, article in enumerate(data, 1):
            try:
                if 'content' in article:
                    article['content'] = self.clean_content(article['content'])
                if 'abstract' in article:
                    article['abstract'] = self.clean_content(article['abstract'])
                
                chunks = processor.process_article(article)
                knowledge_base.extend(chunks)
                
                logging.info(f"Processed article {idx}/{total_articles}")
                
            except Exception as e:
                logging.warning(f"Error processing article {idx}: {str(e)}")
                continue
        
        return knowledge_base

    def process_all(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        for filename in os.listdir(self.input_dir):
            if filename.endswith(('.json', '.txt')):
                knowledge_base = self.process_file(filename)
                output_file = os.path.join(self.output_dir, f"kb_{os.path.splitext(filename)[0]}.json")
                with open(output_file, 'w') as f:
                    json.dump(knowledge_base, f, indent=2)
                logging.info(f"Saved processed knowledge base to {output_file}")

    def test_single_file(self, filename: str):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        knowledge_base = self.process_file(filename)
        output_file = os.path.join(self.output_dir, f"test_kb_{filename}")
        with open(output_file, 'w') as f:
            json.dump(knowledge_base, f, indent=2)
            
        logging.info(f"Test output saved to {output_file}")
        return output_file

if __name__ == "__main__":
    base_dir = "/Users/oli/Documents/GitHub/ADHealth"
    input_dir = os.path.join(base_dir, "scrapped_documents")
    output_dir = os.path.join(base_dir, "rag_system/knowledge_base")
    
    print(f"\nProcessing Knowledge Base")
    print(f"========================")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    print("\nChoose operation mode:")
    print("1. Process all files")
    print("2. Test single file")
    
    try:
        mode = int(input("\nEnter mode (1 or 2): "))
        
        processor = KnowledgeBaseProcessor(input_dir, output_dir)
        
        if mode == 1:
            print("\nProcessing all files...")
            processor.process_all()
            
            print("\nProcessing completed!")
            print("Generated knowledge base files:")
            for file in os.listdir(output_dir):
                if file.startswith('kb_'):
                    print(f"- {file}")
                    
        elif mode == 2:
            available_files = [f for f in os.listdir(input_dir) if f.endswith(('.json', '.txt'))]
            if not available_files:
                print(f"\nError: No JSON or TXT files found in {input_dir}")
                exit(1)
            
            print(f"\nAvailable files to process:")
            for idx, file in enumerate(available_files, 1):
                print(f"{idx}. {file}")
                
            try:
                choice = int(input(f"\nEnter file number (1-{len(available_files)}): "))
                if 1 <= choice <= len(available_files):
                    test_file = available_files[choice - 1]
                else:
                    raise ValueError("Invalid file number")
            except (ValueError, IndexError):
                print(f"\nInvalid choice. Using first available file: {available_files[0]}")
                test_file = available_files[0]
            
            print(f"\nProcessing file: {test_file}")
            
            try:
                output_file = processor.test_single_file(test_file)
                print(f"\nOutput saved to: {output_file}")
                print("\nPreview of processed content:")
                print("-----------------------------")
                
                with open(output_file, 'r') as f:
                    result = json.load(f)
                    print(f"Total chunks processed: {len(result)}")
                    print("\nFirst two chunks preview:")
                    for i, chunk in enumerate(result[:2]):
                        print(f"\nChunk {i+1}:")
                        print(f"- Type: {chunk.get('type', 'unknown')}")
                        print(f"- Title: {chunk.get('title', 'Untitled')}")
                        print(f"- Content preview: {chunk.get('content', '')[:150]}...")
                        
                        topics = chunk.get('topics', [])
                        if topics:
                            print(f"- Topics: {', '.join(topics[:3])}")
                            
                        bullet_points = chunk.get('bullet_points', [])
                        if bullet_points:
                            print(f"- Sample bullet points: {', '.join(bullet_points[:2])}")
                            
                        pub_info = chunk.get('publication_info', {})
                        if pub_info:
                            print("- Publication Info:")
                            if pub_info.get('authors'):
                                print(f"  - Authors: {', '.join(pub_info['authors'][:2])}...")
                            if pub_info.get('journal'):
                                print(f"  - Journal: {pub_info['journal']}")
                            if pub_info.get('year'):
                                print(f"  - Year: {pub_info['year']}")
                
                print("\nDone! Check the output file for complete results.")
                
            except Exception as e:
                print(f"\nError processing file: {str(e)}")
                raise
            
        else:
            print("Invalid mode selected. Please choose 1 or 2.")
            exit(1)
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise

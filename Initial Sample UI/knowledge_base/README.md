# Diabetes Knowledge Base

This directory contains processed knowledge base entries derived from multiple sources including structured JSON and plain text files.

## Input Formats

The knowledge base processor supports multiple input formats:

### JSON Format
Structured data from websites and databases:
- Community content (e.g., ADA website)
- Academic papers (PubMed articles)

### TXT Format
Plain text documents containing relevant information:
- Medical guidelines
- Research notes
- Clinical protocols
- Educational materials

## Output Structure

All processed content is converted to a standardized JSON format:

```json
{
  "content": "The actual knowledge content...",
  "type": "community|academic_abstract|academic_content|text_content",
  "confidence": 0.85-0.95,
  "source": "URL or filename",
  "title": "Document title",
  "topics": ["topic1", "topic2"],
  // Optional fields based on content type:
  "bullet_points": ["point1", "point2"],  // For community content
  "publication_info": {  // For academic content
    "authors": ["author1", "author2"],
    "journal": "journal name",
    "year": "publication year"
  }
}
```

## Usage

The processed knowledge base can be used for:
1. RAG model training and retrieval
2. Multi-source fact verification
3. Cross-reference between academic and community content
4. Comprehensive diabetes information access

## Sources

Content is processed from:
- American Diabetes Association (diabetes.org)
- PubMed academic articles
- Medical text documents
- Other authoritative sources

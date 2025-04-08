# ADHealth Diabetes Management System

ADHealth is an advanced diabetes management platform that combines medical expertise with artificial intelligence to provide personalized insights and recommendations for diabetes patients. The system uses a Retrieval Augmented Generation (RAG) approach to enhance AI responses with domain-specific knowledge.

## Features

- **Multimodal RAG System**: Combines text and image analysis for comprehensive diabetes insights
- **Health Metrics Tracking**: Monitor glucose levels, insulin doses, blood pressure, and carbohydrate intake
- **Personalized AI Insights**: Get contextual recommendations based on your health data
- **Prompt Testing Environment**: Evaluate and refine AI responses for different diabetes-related scenarios
- **Interactive Chat Interface**: Communicate with the AI assistant using both text and images

## System Architecture

### RAG (Retrieval Augmented Generation)

Our system uses a sophisticated RAG approach:

1. **Knowledge Base Processing**: A curated collection of diabetes research, medical guidelines, and clinical information is processed and stored in a vector database.
2. **Query Processing**: User queries are analyzed for intent and context, considering both text and images when available.
3. **Relevant Knowledge Retrieval**: The system retrieves the most relevant information from the knowledge base.
4. **Augmented Generation**: The retrieved information augments the AI's response, ensuring medical accuracy and personalized insights.

### Multimodal Capabilities

The system can process:

- Text queries about diabetes management
- Images of glucose meters and readings
- Food photos for carbohydrate estimation
- Medical documents and charts
- Continuous glucose monitor (CGM) graphs

## Getting Started

### Prerequisites

- Python 3.8+
- Flask
- SQLite
- OpenAI API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/adhealth.git
   cd adhealth
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   export OPENAI_API_KEY=your_api_key
   export FLASK_SECRET_KEY=your_secret_key
   ```

4. Initialize the database:
   ```
   python app.py
   ```

5. Access the web application:
   ```
   http://localhost:5001
   ```

## Usage

### Dashboard

The dashboard provides a comprehensive view of your health metrics with AI-generated insights.

### Prompt Testing

The prompt testing page allows you to experiment with different types of diabetes-related queries to see how the AI responds. This is useful for:

- Understanding what questions yield the most helpful information
- Evaluating the AI's medical knowledge and relevance
- Testing the system's ability to handle different scenarios

### Chat Interface

The chat interface provides a conversational way to interact with the AI assistant. You can:

- Ask questions about diabetes management
- Upload images for analysis
- Get personalized recommendations based on your health data

## Knowledge Base

The system's knowledge base includes information from:

- American Diabetes Association guidelines
- Clinical research on diabetes management
- Nutritional information for diabetes
- Exercise recommendations
- Medication guidance

## Contributing

Contributions to improve the system are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT models
- LangChain for RAG implementation
- Flask community for web framework
- Contributors and diabetes specialists who provided domain expertise 
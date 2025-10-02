# 🤖 Hybrid AI Agent

Agentic knowledge retrieval redefined with an AI agent system that combines traditional RAG (vector search) with knowledge graph capabilities to analyze and provide insights about big tech companies and their AI initiatives. The system uses PostgreSQL with pgvector for semantic search and Neo4j with Graphiti for temporal knowledge graphs. The goal is to create Agentic RAG at its finest.

***

## Built with:

- Pydantic AI for the AI Agent Framework  
- Graphiti for the Knowledge Graph  
- Postgres with PGVector for the Vector Database  
- Neo4j for the Knowledge Graph Engine (Graphiti connects to this)  
- FastAPI for the Agent API  
- Perplexity AI for Web Search Integration  
- Claude Code for the AI Coding Assistant (See CLAUDE.md, PLANNING.md, and TASK.md)  

***

## Overview

This system includes three main components:

- **Document Ingestion Pipeline**: Processes markdown documents using semantic chunking and builds both vector embeddings and knowledge graph relationships  
- **AI Agent Interface**: A conversational agent powered by Pydantic AI that can search across both vector database and knowledge graph  
- **Streaming API**: FastAPI backend with real-time streaming responses and comprehensive search capabilities  

***

## Prerequisites

- Python 3.11 or higher  
- PostgreSQL database (such as Neon)  
- Neo4j database (for knowledge graph)  
- LLM Provider API key (OpenAI, Ollama, Gemini, etc.)  
- Perplexity API key (optional - for web search functionality)  

***

## Installation

### 1. Set up a virtual environment

```bash
python -m venv venv       # python3 on Linux
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate     # On Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up required tables in Postgres

Execute the SQL in `sql/schema.sql` to create all necessary tables, indexes, and functions.  

Be sure to change the embedding dimensions on lines 31, 67, and 100 based on your embedding model. OpenAI's `text-embedding-3-small` is 1536 and `nomic-embed-text` from Ollama is 768 dimensions, for reference.  

**Note:** This script will drop all tables before creating/recreating!

### 4. Set up Neo4j
#### Option A: Using Local-AI-Packaged (Recommended)
Follow the installation instructions to set up Neo4j through the package. Note the username, password, and URI (`bolt://localhost:7687`).  

#### Option B: Using Neo4j Desktop

- Download and install Neo4j Desktop  
- Create a new project and add a local DBMS  
- Start the DBMS and set a password  
- Note the connection details (URI, username, password)  

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
# Database Configuration (example Neon connection string)
DATABASE_URL=postgresql://username:password@ep-example-12345.us-east-2.aws.neon.tech/neondb

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# LLM Provider Configuration (choose one)
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-api-key
LLM_CHOICE=gpt-4.1-mini

# Embedding Configuration
EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-your-api-key
EMBEDDING_MODEL=text-embedding-3-small

# Ingestion Configuration
INGESTION_LLM_CHOICE=gpt-4.1-nano

# Perplexity Configuration (optional - for web search)
PERPLEXITY_API_KEY=pplx-your-api-key
PERPLEXITY_MODEL=llama-3.1-sonar-large-128k-online

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
APP_PORT=8058
```

For other LLM providers, see examples in the original description.  

***

## Quick Start

### 1. Prepare Your Documents

```bash
mkdir -p documents
```

Add your markdown files about tech companies and AI research to the `documents/` directory. Example:  

- `documents/google_ai_initiatives.md`  
- `documents/microsoft_openai_partnership.md`  

You may also copy the provided `big_tech_docs` folder for a richer dataset:  

```bash
cp -r big_tech_docs/* documents/
```

### 2. Run Document Ingestion

```bash
# Basic ingestion with semantic chunking
python -m ingestion.ingest

# Clean existing data and re-ingest everything
python -m ingestion.ingest --clean

# Custom faster processing (no knowledge graph)
python -m ingestion.ingest --chunk-size 800 --no-semantic --verbose
```

The ingestion process will parse documents, chunk them, generate embeddings, extract entities, build relationships, and store everything in both PostgreSQL and Neo4j.  

### 3. Configure Agent Behavior (Optional)

Modify the system prompt in `agent/prompts.py` to adjust tool usage and reasoning.

### 4. Start the API Server

```bash
python -m agent.api
```

Access at: [http://localhost:8058](http://localhost:8058)

### 5. Use the CLI

```bash
python cli.py
```

With options for port and URL customization.  

***

## Example CLI Session

```
🤖 Agentic RAG with Knowledge Graph CLI
============================================================
Connected to: http://localhost:8058

You: What are Microsoft's AI initiatives?

🤖 Assistant:
Microsoft has several major AI initiatives including...

🛠 Tools Used:
 1. vector_search (query='Microsoft AI initiatives', limit=10)
 2. graph_search (query='Microsoft AI projects')

────────────────────────────────────────────────────────────

You: How is Microsoft connected to OpenAI?

🤖 Assistant:
Microsoft has a significant strategic partnership with OpenAI...

🛠 Tools Used:
 1. hybrid_search (query='Microsoft OpenAI partnership', limit=10)
 2. get_entity_relationships (entity='Microsoft')
```

***

## Example Queries

- "What AI research is Google working on?" → Vector Search  
- "How are Microsoft and OpenAI connected?" → Knowledge Graph  
- "Show me the timeline of Meta's AI announcements" → Temporal Graph Search  
- "Compare the AI strategies of FAANG companies" → Hybrid Search  

***

## Project Structure

```
agentic-rag-knowledge-graph/
├── agent/              # AI agent and API
│   ├── agent.py        # Main Pydantic AI agent
│   ├── api.py          # FastAPI application
│   ├── providers.py    # LLM provider abstraction
│   ├── models.py       # Data models
│   ├── tools.py        # Agent tools (search, graph, web)
│   ├── db_utils.py     # PostgreSQL utilities
│   ├── graph_utils.py  # Neo4j/Graphiti utilities
│   ├── web_utils.py    # Perplexity web search
│   └── prompts.py      # Agent prompts
├── ingestion/          # Document processing
│   ├── ingest.py       # Main ingestion pipeline
│   ├── chunker.py      # Semantic chunking
│   ├── embedder.py     # Embedding generation
│   └── graph_builder.py# Knowledge graph construction
├── sql/                # Database schema
├── documents/          # Markdown files
├── cli.py              # Interactive command-line interface
└── tests/              # Comprehensive test suite
```

***

## Advanced Features

- **Web Search Integration** with Perplexity AI  
- **Entity Extraction** for companies, technologies, people, and locations  
- **Efficient Database Connection Pooling**  
- **Graphiti Temporal Knowledge Graph** for time-evolving facts  

***

## Troubleshooting

- **Database Connection Issues**: Verify `DATABASE_URL`  
- **Neo4j Connection Issues**: Ensure service is running and credentials are correct  
- **Agent Returning No Results**: Run ingestion first  
- **LLM API Issues**: Check `.env` values  
- **Knowledge Graph Token Issues**: Large documents are automatically truncated  

***

## Testing

```bash
pytest
pytest --cov=agent --cov=ingestion --cov-report=html
```

***

## Available Agent Tools

- **Search**: `vector_search`, `graph_search`, `hybrid_search`, `web_search`  
- **Graph**: `get_entity_relationships`, `get_entity_timeline`  
- **Documents**: `get_document`, `list_documents`, `get_document_chunks`  

***

## Key Features

- Hybrid Search combining vectors + graphs  
- Temporal Knowledge Graphs (via Graphiti)  
- Real-time Web Search with Perplexity AI  
- Streaming Responses with Server-Sent Events  
- Multi-provider LLM Support (OpenAI, Ollama, OpenRouter, Gemini)  
- Intelligent Semantic Chunking  
- Production Ready logging, monitoring, and error handling  

***

**Built with ❤️ using Pydantic AI, FastAPI, PostgreSQL, Neo4j, Graphiti, and Perplexity AI.**
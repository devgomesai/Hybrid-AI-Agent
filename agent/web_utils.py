"""
Perplexity AI web search tool with database integration.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

import httpx
from dotenv import load_dotenv

from .db_utils import db_pool, add_message

load_dotenv()

logger = logging.getLogger(__name__)


class PerplexitySearchTool:
    """Web search tool using Perplexity AI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Perplexity search tool.
        
        Args:
            api_key: Perplexity API key (defaults to PERPLEXITY_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable not set")
        
        self.base_url = "https://api.perplexity.ai"
        self.default_model = os.getenv("PERPLEXITY_MODEL")
        self.timeout = 60.0
    
    async def search(
        self,
        query: str,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        top_p: float = 0.9,
        return_citations: bool = True,
        return_images: bool = False,
        search_domain_filter: Optional[List[str]] = None,
        search_recency_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform web search using Perplexity AI.
        
        Args:
            query: Search query
            model: Model to use (default: llama-3.1-sonar-large-128k-online)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            return_citations: Include citations in response
            return_images: Include images in response
            search_domain_filter: List of domains to search within
            search_recency_filter: Time filter (month, week, day, hour)
        
        Returns:
            Search results with answer and citations
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or self.default_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Be precise and concise. Provide accurate information with proper citations."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "return_citations": return_citations,
            "return_images": return_images,
            "stream": False
        }
        
        # Add optional search filters
        if search_domain_filter:
            payload["search_domain_filter"] = search_domain_filter
        
        if search_recency_filter:
            payload["search_recency_filter"] = search_recency_filter
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return self._parse_response(result, query)
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def _parse_response(self, response: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Parse Perplexity API response.
        
        Args:
            response: API response
            query: Original query
        
        Returns:
            Structured search results
        """
        choices = response.get("choices", [])
        if not choices:
            return {
                "query": query,
                "answer": "",
                "citations": [],
                "images": [],
                "usage": response.get("usage", {}),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        message = choices[0].get("message", {})
        content = message.get("content", "")
        
        return {
            "query": query,
            "answer": content,
            "citations": response.get("citations", []),
            "images": response.get("images", []),
            "usage": response.get("usage", {}),
            "model": response.get("model", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def search_with_session(
        self,
        session_id: str,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform search and store results in session.
        
        Args:
            session_id: Session UUID
            query: Search query
            **kwargs: Additional search parameters
        
        Returns:
            Search results
        """
        # Add user query to messages
        await add_message(
            session_id=session_id,
            role="user",
            content=query,
            metadata={"type": "search_query"}
        )
        
        # Perform search
        results = await self.search(query, **kwargs)
        
        # Store search results as assistant message
        await add_message(
            session_id=session_id,
            role="assistant",
            content=results["answer"],
            metadata={
                "type": "search_result",
                "citations": results["citations"],
                "images": results["images"],
                "usage": results["usage"],
                "model": results["model"]
            }
        )
        
        return results
    
    async def multi_search(
        self,
        queries: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform multiple searches concurrently.
        
        Args:
            queries: List of search queries
            **kwargs: Additional search parameters
        
        Returns:
            List of search results
        """
        tasks = [self.search(query, **kwargs) for query in queries]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def search_with_context(
        self,
        query: str,
        context_messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform search with conversation context.
        
        Args:
            query: Search query
            context_messages: Previous conversation messages
            **kwargs: Additional search parameters
        
        Returns:
            Search results
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build messages with context
        messages = [
            {
                "role": "system",
                "content": "Be precise and concise. Provide accurate information with proper citations."
            }
        ]
        
        # Add context messages (limit to last 5 exchanges)
        messages.extend(context_messages[-10:])
        
        # Add current query
        messages.append({
            "role": "user",
            "content": query
        })
        
        payload = {
            "model": kwargs.get("model", self.default_model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.2),
            "top_p": kwargs.get("top_p", 0.9),
            "return_citations": kwargs.get("return_citations", True),
            "return_images": kwargs.get("return_images", False),
            "stream": False
        }
        
        # Add optional filters
        if "search_domain_filter" in kwargs:
            payload["search_domain_filter"] = kwargs["search_domain_filter"]
        
        if "search_recency_filter" in kwargs:
            payload["search_recency_filter"] = kwargs["search_recency_filter"]
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return self._parse_response(result, query)
        
        except Exception as e:
            logger.error(f"Context search failed: {e}")
            raise


# Database integration functions
async def store_search_result(
    search_result: Dict[str, Any],
    session_id: Optional[str] = None
) -> str:
    """
    Store search result as a document in database.
    
    Args:
        search_result: Search result from Perplexity
        session_id: Optional session ID
    
    Returns:
        Document ID
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO documents (title, source, content, metadata)
            VALUES ($1, $2, $3, $4)
            RETURNING id::text
            """,
            f"Search: {search_result['query'][:100]}",
            "perplexity_search",
            search_result["answer"],
            json.dumps({
                "query": search_result["query"],
                "citations": search_result["citations"],
                "images": search_result["images"],
                "usage": search_result["usage"],
                "model": search_result["model"],
                "timestamp": search_result["timestamp"],
                "session_id": session_id
            })
        )
        
        return result["id"]


async def get_search_history(
    session_id: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get search history for a session.
    
    Args:
        session_id: Session UUID
        limit: Maximum number of results
    
    Returns:
        List of search results
    """
    async with db_pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT 
                id::text,
                content,
                metadata,
                created_at
            FROM messages
            WHERE session_id = $1::uuid
            AND role = 'assistant'
            AND metadata->>'type' = 'search_result'
            ORDER BY created_at DESC
            LIMIT $2
            """,
            session_id,
            limit
        )
        
        return [
            {
                "id": row["id"],
                "answer": row["content"],
                "metadata": json.loads(row["metadata"]),
                "created_at": row["created_at"].isoformat()
            }
            for row in results
        ]

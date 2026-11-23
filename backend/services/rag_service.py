import os
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from fastembed import TextEmbedding
from flashrank import Ranker, RerankRequest
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class RAGService:
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "bpie_college_policies",
        local_path: Optional[str] = None,
        embedding_model_name: str = "BAAI/bge-small-en-v1.5",
        reranker_model_name: str = "ms-marco-TinyBERT-L-2-v2",
        groq_api_key: Optional[str] = None,
        groq_model: str = "openai/gpt-oss-120b"
    ):
        self.collection_name = collection_name
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.groq_model = groq_model

        # 1. Initialize FastEmbed (CPU optimized, 0 cost, no GPU required)
        print(f"[RAGService] Loading FastEmbed model: {embedding_model_name}")
        self.embedding_model = TextEmbedding(model_name=embedding_model_name)
        # BGE-small-en-v1.5 produces 384 dimensional vectors
        self.vector_dim = 384

        # 2. Initialize Qdrant Client (Cloud or Local disk)
        if qdrant_url and qdrant_url.strip():
            print(f"[RAGService] Connecting to Qdrant Cloud at: {qdrant_url}")
            self.qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key or None)
        else:
            storage_path = local_path or os.path.join(os.path.dirname(__file__), "..", "qdrant_storage")
            os.makedirs(storage_path, exist_ok=True)
            print(f"[RAGService] Using local disk Qdrant storage at: {storage_path}")
            self.qdrant_client = QdrantClient(path=storage_path)

        self._ensure_collection()

        # 3. Initialize FlashRank Reranker (High quality, production grade, local CPU)
        print(f"[RAGService] Loading FlashRank Reranker: {reranker_model_name}")
        try:
            self.reranker = Ranker(model_name=reranker_model_name)
        except Exception as e:
            print(f"[RAGService] FlashRank init warning ({e}). Falling back to default ranker.")
            self.reranker = Ranker()

        # 4. Initialize Groq LLM
        if self.groq_api_key:
            self.llm = ChatGroq(
                groq_api_key=self.groq_api_key,
                model_name=self.groq_model,
                temperature=0.1
            )
        else:
            self.llm = None
            print("[RAGService] WARNING: GROQ_API_KEY is not configured.")

    def _ensure_collection(self):
        """
        Verify collection exists in Qdrant; if not, create it.
        """
        try:
            collections = self.qdrant_client.get_collections().collections
            exists = any(col.name == self.collection_name for col in collections)
            if not exists:
                print(f"[RAGService] Creating Qdrant collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_dim,
                        distance=qmodels.Distance.COSINE
                    )
                )
        except Exception as e:
            print(f"[RAGService] Collection verification error: {e}")

    def index_chunks(self, document_id: str, document_title: str, chunks: List[Dict[str, Any]]) -> int:
        """
        Embed and index chunks into Qdrant vector database.
        """
        if not chunks:
            return 0

        texts = [chunk["text"] for chunk in chunks]
        embeddings = list(self.embedding_model.embed(texts))

        points = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            payload = {
                "document_id": document_id,
                "document_title": document_title,
                "text": chunk["text"],
                "page": chunk["metadata"].get("page", 1),
                "chunk_index": chunk["metadata"].get("chunk_index", i)
            }
            points.append(qmodels.PointStruct(
                id=point_id,
                vector=emb.tolist(),
                payload=payload
            ))

        # Batch upsert points in chunks of 100
        batch_size = 100
        total_indexed = 0
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            total_indexed += len(batch)

        print(f"[RAGService] Indexed {total_indexed} points for doc '{document_title}'")
        return total_indexed

    def delete_document_points(self, document_id: str):
        """
        Remove all vector points associated with a specific document from Qdrant.
        """
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="document_id",
                                match=qmodels.MatchValue(value=document_id)
                            )
                        ]
                    )
                )
            )
            print(f"[RAGService] Deleted Qdrant points for document_id={document_id}")
        except Exception as e:
            print(f"[RAGService] Error deleting points: {e}")

    def retrieve_and_rerank(self, query: str, top_k_initial: int = 12, top_k_final: int = 4) -> List[Dict[str, Any]]:
        """
        Two-stage retrieval:
        1. Fast vector similarity search in Qdrant (top 12 candidates).
        2. FlashRank cross-encoder reranking to pick top 4 high-relevance chunks.
        """
        query_embedding = list(self.embedding_model.embed([query]))[0].tolist()

        try:
            if hasattr(self.qdrant_client, "query_points"):
                response = self.qdrant_client.query_points(
                    collection_name=self.collection_name,
                    query=query_embedding,
                    limit=top_k_initial,
                    with_payload=True
                )
                search_results = response.points
            else:
                search_results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=top_k_initial,
                    with_payload=True
                )
        except Exception as e:
            print(f"[RAGService] Vector search error: {e}")
            return []

        if not search_results:
            return []

        # Prepare candidates for FlashRank
        passages = []
        for i, hit in enumerate(search_results):
            payload = hit.payload or {}
            passages.append({
                "id": i,
                "text": payload.get("text", ""),
                "meta": {
                    "document_title": payload.get("document_title", "Unknown Policy Document"),
                    "page": payload.get("page", 1),
                    "chunk_index": payload.get("chunk_index", 0),
                    "qdrant_score": hit.score
                }
            })

        # Stage 2: Cross-Encoder Reranking
        try:
            rerank_request = RerankRequest(query=query, passages=passages)
            ranked_results = self.reranker.rerank(rerank_request)
            top_ranked = ranked_results[:top_k_final]

            final_chunks = []
            for item in top_ranked:
                meta = item.get("meta", {})
                final_chunks.append({
                    "text": item.get("text", ""),
                    "document_title": meta.get("document_title", "Unknown"),
                    "page": meta.get("page", 1),
                    "relevance_score": float(item.get("score", 0.0))
                })
            return final_chunks
        except Exception as e:
            print(f"[RAGService] Reranker error ({e}). Returning initial vector results.")
            # Fallback to initial search results
            return [
                {
                    "text": hit.payload.get("text", ""),
                    "document_title": hit.payload.get("document_title", "Unknown"),
                    "page": hit.payload.get("page", 1),
                    "relevance_score": float(hit.score)
                }
                for hit in search_results[:top_k_final]
            ]

    def answer_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Execute full RAG generation pipeline with conversation memory & multi-language support.
        """
        if not self.llm:
            return {
                "answer": "Groq LLM is not configured. Please supply a valid GROQ_API_KEY in the backend .env.",
                "sources": []
            }

        # Step 1: Retrieve & Rerank Chunks
        retrieved_chunks = self.retrieve_and_rerank(query)

        # Build context block with citations
        context_parts = []
        sources = []
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            doc = chunk["document_title"]
            page = chunk["page"]
            text = chunk["text"]
            context_parts.append(f"--- [Source {idx}]: {doc} (Page {page}) ---\n{text}")
            sources.append({
                "source_id": idx,
                "document": doc,
                "page": page,
                "snippet": text[:200] + "..." if len(text) > 200 else text
            })

        context_str = "\n\n".join(context_parts) if context_parts else "No policy documents currently indexed."

        # Map language codes to clear instructions
        lang_instructions = {
            "en": "Respond in clear, professional English.",
            "bn": "Respond fluently in Bengali (বাংলা). Maintain official policy terms accurately.",
            "hi": "Respond fluently in Hindi (हिंदी). Maintain official policy terms accurately."
        }
        lang_note = lang_instructions.get(language.lower(), f"Respond in language code: {language}.")

        system_prompt = f"""You are the official AI Policy Agent for Bishnupur Public Institute of Engineering (BPIE), located in Bishnupur, Bankura (Estd. 2010, A Polytechnic College).
Your purpose is to assist students, faculty, and administrative staff by answering questions strictly based on the provided official college rules, academic regulations, examination guidelines, anti-ragging policies, hostel rules, and disciplinary procedures.

GUIDELINES:
1. Grounding: Rely strictly on the official context provided below. Do not fabricate or speculate on college rules.
2. Anti-Hallucination: If the answer cannot be found in the provided policy excerpts, clearly and politely inform the user that this policy is not covered in the currently indexed documents, and advise them to consult the BPIE Administrative Office or Academic Cell.
3. Citations: When referencing rules, explicitly cite the document title and page number (e.g. "[Source 1: Academic Regulations, Page 4]").
4. Tone: Courteous, official, supportive, and precise.
5. Language: {lang_note}

OFFICIAL POLICY CONTEXT:
{context_str}
"""

        messages = [SystemMessage(content=system_prompt)]

        # Append recent conversation history (last 6 messages) for context
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))

        # Add current user query
        messages.append(HumanMessage(content=query))

        try:
            response = self.llm.invoke(messages)
            answer_text = response.content.strip()
        except Exception as e:
            print(f"[RAGService] Groq error with {self.groq_model}: {e}. Trying fallback to llama-3.3-70b-versatile...")
            try:
                fallback_llm = ChatGroq(
                    groq_api_key=self.groq_api_key,
                    model_name="llama-3.3-70b-versatile",
                    temperature=0.1
                )
                response = fallback_llm.invoke(messages)
                answer_text = response.content.strip()
            except Exception as e2:
                answer_text = f"An error occurred while generating the answer from Groq: {str(e2)}"

        return {
            "answer": answer_text,
            "sources": sources
        }

"""
Assistant RAG (Retrieval-Augmented Generation) pour SmartMarket.
"""

import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from .config import (
    RAG_INDEX_PATH,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP,
    RAG_TOP_K,
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_MAX_TOKENS,
)


class RAGDocument:
    """Représente un document pour le RAG."""
    
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le document en dictionnaire."""
        return {
            'id': self.id,
            'content': self.content,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
        }


class RAGChunker:
    """Classe pour découper les documents en chunks."""
    
    def __init__(self, chunk_size: int = RAG_CHUNK_SIZE, overlap: int = RAG_CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Découpe un texte en chunks avec overlap.
        
        Args:
            text: Texte à découper
            
        Returns:
            Liste des chunks
        """
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        start = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            
            if end == len(words):
                break
            
            start = end - self.overlap
        
        return chunks
    
    def chunk_document(self, document: RAGDocument) -> List[RAGDocument]:
        """
        Découpe un document en chunks.
        
        Args:
            document: Document à découper
            
        Returns:
            Liste des chunks
        """
        chunks = self.chunk_text(document.content)
        
        chunk_documents = []
        for i, chunk_content in enumerate(chunks):
            chunk_metadata = document.metadata.copy()
            chunk_metadata.update({
                'chunk_index': i,
                'total_chunks': len(chunks),
                'parent_document_id': document.id,
            })
            
            chunk_doc = RAGDocument(chunk_content, chunk_metadata)
            chunk_documents.append(chunk_doc)
        
        return chunk_documents


class RAGIndex:
    """Index vectoriel pour le RAG."""
    
    def __init__(self):
        self.index: Optional[faiss.Index] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        self.documents: List[RAGDocument] = []
        self.document_embeddings: Optional[np.ndarray] = None
        self.chunker = RAGChunker()
    
    def load_embedding_model(self):
        """Charge le modèle d'embeddings."""
        try:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as e:
            print(f"Erreur lors du chargement du modèle d'embeddings: {e}")
            self.embedding_model = None
    
    def add_documents(self, documents: List[RAGDocument]):
        """
        Ajoute des documents à l'index.
        
        Args:
            documents: Liste des documents à ajouter
        """
        if not self.embedding_model:
            raise ValueError("Modèle d'embeddings non chargé")
        
        # Découper les documents
        all_chunks = []
        for doc in documents:
            chunks = self.chunker.chunk_document(doc)
            all_chunks.extend(chunks)
        
        if not all_chunks:
            return
        
        # Générer les embeddings
        chunk_texts = [chunk.content for chunk in all_chunks]
        embeddings = self.embedding_model.encode(
            chunk_texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Créer ou mettre à jour l'index
        if self.index is None:
            self.index = faiss.IndexFlatIP(embeddings.shape[1])
            self.documents = []
            self.document_embeddings = embeddings
        else:
            self.document_embeddings = np.vstack([self.document_embeddings, embeddings])
            self.index.add(embeddings.astype('float32'))
        
        # Ajouter les documents
        self.documents.extend(all_chunks)
        
        # Normaliser les embeddings pour la similarité cosinus
        faiss.normalize_L2(self.document_embeddings)
    
    def search(self, query: str, k: int = RAG_TOP_K) -> List[Tuple[RAGDocument, float]]:
        """
        Recherche dans l'index RAG.
        
        Args:
            query: Requête de recherche
            k: Nombre de résultats à retourner
            
        Returns:
            Liste de tuples (document, score)
        """
        if self.index is None or self.embedding_model is None:
            raise ValueError("Index ou modèle d'embeddings non chargé")
        
        # Générer l'embedding de la requête
        query_embedding = self.embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Rechercher dans l'index
        scores, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Formater les résultats
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # Index invalide
                continue
            
            if idx < len(self.documents):
                document = self.documents[idx]
                results.append((document, float(score)))
        
        return results
    
    def save_index(self):
        """Sauvegarde l'index et les documents."""
        if self.index is None:
            return
        
        # Sauvegarder l'index FAISS
        faiss.write_index(self.index, str(RAG_INDEX_PATH))
        
        # Sauvegarder les documents
        documents_data = [doc.to_dict() for doc in self.documents]
        documents_path = RAG_INDEX_PATH.with_suffix('.documents.json')
        with open(documents_path, 'w', encoding='utf-8') as f:
            json.dump(documents_data, f, ensure_ascii=False, indent=2)
        
        # Sauvegarder les embeddings
        if self.document_embeddings is not None:
            embeddings_path = RAG_INDEX_PATH.with_suffix('.embeddings.npy')
            np.save(embeddings_path, self.document_embeddings)
    
    def load_index(self):
        """Charge l'index et les documents."""
        if not RAG_INDEX_PATH.exists():
            return False
        
        try:
            # Charger l'index FAISS
            self.index = faiss.read_index(str(RAG_INDEX_PATH))
            
            # Charger les documents
            documents_path = RAG_INDEX_PATH.with_suffix('.documents.json')
            if documents_path.exists():
                with open(documents_path, 'r', encoding='utf-8') as f:
                    documents_data = json.load(f)
                
                self.documents = []
                for doc_data in documents_data:
                    doc = RAGDocument(doc_data['content'], doc_data['metadata'])
                    doc.id = doc_data['id']
                    doc.created_at = datetime.fromisoformat(doc_data['created_at'])
                    self.documents.append(doc)
            
            # Charger les embeddings
            embeddings_path = RAG_INDEX_PATH.with_suffix('.embeddings.npy')
            if embeddings_path.exists():
                self.document_embeddings = np.load(embeddings_path)
            
            return True
        except Exception as e:
            print(f"Erreur lors du chargement de l'index RAG: {e}")
            return False


class RAGAssistant:
    """Assistant RAG pour SmartMarket."""
    
    def __init__(self):
        self.rag_index = RAGIndex()
        self.openai_client = None
        self._setup_openai()
    
    def _setup_openai(self):
        """Configure le client OpenAI."""
        if OPENAI_API_KEY:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
            except ImportError:
                print("OpenAI non installé. L'assistant RAG ne fonctionnera pas.")
            except Exception as e:
                print(f"Erreur lors de la configuration d'OpenAI: {e}")
    
    def load_index(self):
        """Charge l'index RAG."""
        self.rag_index.load_embedding_model()
        return self.rag_index.load_index()
    
    def add_knowledge_base(self, documents: List[RAGDocument]):
        """
        Ajoute une base de connaissances.
        
        Args:
            documents: Liste des documents à ajouter
        """
        self.rag_index.load_embedding_model()
        self.rag_index.add_documents(documents)
        self.rag_index.save_index()
    
    def ask(self, question: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Pose une question à l'assistant RAG.
        
        Args:
            question: Question de l'utilisateur
            user_context: Contexte utilisateur (optionnel)
            
        Returns:
            Dictionnaire avec la réponse et les métadonnées
        """
        trace_id = str(uuid.uuid4())
        
        try:
            # Rechercher des documents pertinents
            relevant_docs = self.rag_index.search(question, k=RAG_TOP_K)
            
            if not relevant_docs:
                return {
                    'answer': "Je n'ai pas trouvé d'informations pertinentes pour répondre à votre question dans notre base de connaissances.",
                    'sources': [],
                    'trace_id': trace_id,
                    'confidence': 0.0,
                    'status': 'no_sources'
                }
            
            # Construire le contexte
            context = self._build_context(relevant_docs)
            
            # Générer la réponse
            if self.openai_client:
                answer = self._generate_answer_with_llm(question, context)
            else:
                answer = self._generate_simple_answer(question, relevant_docs)
            
            # Préparer les sources
            sources = [
                {
                    'content': doc.content[:200] + '...' if len(doc.content) > 200 else doc.content,
                    'metadata': doc.metadata,
                    'score': score
                }
                for doc, score in relevant_docs
            ]
            
            return {
                'answer': answer,
                'sources': sources,
                'trace_id': trace_id,
                'confidence': relevant_docs[0][1] if relevant_docs else 0.0,
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'answer': "Une erreur s'est produite lors du traitement de votre question.",
                'sources': [],
                'trace_id': trace_id,
                'confidence': 0.0,
                'status': 'error',
                'error': str(e)
            }
    
    def _build_context(self, relevant_docs: List[Tuple[RAGDocument, float]]) -> str:
        """
        Construit le contexte à partir des documents pertinents.
        
        Args:
            relevant_docs: Documents pertinents avec scores
            
        Returns:
            Contexte formaté
        """
        context_parts = []
        
        for i, (doc, score) in enumerate(relevant_docs, 1):
            context_parts.append(f"Source {i} (score: {score:.3f}):\n{doc.content}")
        
        return "\n\n".join(context_parts)
    
    def _generate_answer_with_llm(self, question: str, context: str) -> str:
        """
        Génère une réponse avec un LLM.
        
        Args:
            question: Question de l'utilisateur
            context: Contexte des documents
            
        Returns:
            Réponse générée
        """
        if not self.openai_client:
            return self._generate_simple_answer(question, [])
        
        try:
            prompt = f"""Tu es un assistant d'aide à l'achat pour SmartMarket, un site e-commerce.

Contexte (informations de la base de connaissances):
{context}

Question de l'utilisateur: {question}

Instructions:
- Réponds uniquement en français
- Base ta réponse uniquement sur le contexte fourni
- Si l'information n'est pas dans le contexte, dis-le clairement
- Sois concis et utile
- Ne mentionne pas que tu es une IA

Réponse:"""

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=OPENAI_MAX_TOKENS,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Erreur lors de la génération de réponse: {e}")
            return self._generate_simple_answer(question, [])
    
    def _generate_simple_answer(self, question: str, relevant_docs: List[Tuple[RAGDocument, float]]) -> str:
        """
        Génère une réponse simple sans LLM.
        
        Args:
            question: Question de l'utilisateur
            relevant_docs: Documents pertinents
            
        Returns:
            Réponse simple
        """
        if not relevant_docs:
            return "Je n'ai pas trouvé d'informations pertinentes pour répondre à votre question."
        
        # Prendre le document le plus pertinent
        best_doc, best_score = relevant_docs[0]
        
        if best_score > 0.7:
            return f"Voici les informations que j'ai trouvées :\n\n{best_doc.content}"
        else:
            return "J'ai trouvé des informations partiellement pertinentes, mais je ne peux pas donner une réponse complète à votre question."


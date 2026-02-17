import os
from pinecone import Pinecone, ServerlessSpec
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.postprocessor.sbert_rerank import SentenceTransformerRerank
from llama_parse import LlamaParse
from src.core.config import config


class VectorKnowledgeBase:
    def __init__(self):
        self.pc = Pinecone(api_key=config.PINECONE_API_KEY)
        self.index_name = config.PINECONE_INDEX_NAME
        self.ensure_index_exists()
        self.vector_store = PineconeVectorStore(pinecone_index=self.pc.Index(self.index_name))
        self.embed_model = OpenAIEmbedding(model=config.EMBEDDING_MODEL)
        self.llm = OpenAI(model=config.MODEL_NAME, temperature=config.TEMPERATURE)
        self.reranker = SentenceTransformerRerank(
            model="cross-encoder/ms-marco-MiniLM-L-12-v2",
            top_n=8
        )
        self.index = None

    def ensure_index_exists(self):
        existing_indexes = [i.name for i in self.pc.list_indexes()]
        if self.index_name not in existing_indexes:
            print(f"[RAG] Creando indice en Pinecone: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=config.EMBEDDING_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        else:
            print(f"[RAG] Indice existente: {self.index_name}")

    def ingest_manuals(self):
        print("[RAG] Iniciando ingesta de manuales con LlamaParse...")
        parser = LlamaParse(
            api_key=config.LLAMA_CLOUD_API_KEY,
            result_type="markdown",
            verbose=True,
            language="en",
        )
        file_extractor = {".pdf": parser}
        reader = SimpleDirectoryReader(
            input_dir=config.MANUALS_DIR,
            file_extractor=file_extractor
        )
        documents = reader.load_data()
        print(f"[RAG] {len(documents)} documentos cargados. Indexando en Pinecone...")

        from llama_index.core.node_parser import SentenceSplitter
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=self.embed_model,
            transformations=[SentenceSplitter(chunk_size=1024, chunk_overlap=200)]
        )
        print("[RAG] Ingesta completada.")

    def ingest_file(self, filepath: str):
        print(f"[RAG] Ingesta incremental: {os.path.basename(filepath)}")
        if filepath.endswith(".pdf"):
            parser = LlamaParse(
                api_key=config.LLAMA_CLOUD_API_KEY,
                result_type="markdown",
                verbose=True,
                language="en",
            )
            reader = SimpleDirectoryReader(
                input_files=[filepath],
                file_extractor={".pdf": parser}
            )
        else:
            reader = SimpleDirectoryReader(input_files=[filepath])

        documents = reader.load_data()
        print(f"[RAG] {len(documents)} fragmentos cargados desde {os.path.basename(filepath)}.")

        from llama_index.core.node_parser import SentenceSplitter
        splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
        nodes = splitter.get_nodes_from_documents(documents)

        if not self.index:
            self.index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                embed_model=self.embed_model
            )

        self.index.insert_nodes(nodes)
        print(f"[RAG] {len(nodes)} nodos insertados en Pinecone.")

    def _rewrite_query(self, query_text: str, llm) -> list:
        rewrite_prompt = (
            "You are a search query optimizer for technical documentation about PostgreSQL, Docker, and Nginx.\n"
            "The documents are written in BOTH English and Spanish.\n"
            "Given the user's question, generate exactly 5 search queries that would find the most relevant documentation sections.\n"
            "Rules:\n"
            "- Query 1: Rephrase in English using official doc terminology\n"
            "- Query 2: Rephrase in Spanish using technical terminology\n"
            "- Query 3: Use specific section names, table names, or chapter references from docs\n"
            "- Query 4: List the specific keywords/values the answer would contain (e.g., function names, constants, config params)\n"
            "- Query 5: Alternative interpretation — rephrase as a different but related question\n"
            "Return ONLY the 5 queries, one per line, no numbering, no explanation.\n\n"
            f"User question: {query_text}"
        )
        response = llm.complete(rewrite_prompt)
        queries = [q.strip() for q in str(response).strip().split("\n") if q.strip()]
        queries.insert(0, query_text)
        return queries[:6]

    def query(self, query_text: str) -> str:
        if not self.index:
            self.index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                embed_model=self.embed_model
            )

        search_queries = self._rewrite_query(query_text, self.llm)

        retriever = self.index.as_retriever(similarity_top_k=5)
        all_nodes = []
        seen_ids = set()
        for sq in search_queries:
            nodes = retriever.retrieve(sq)
            for node in nodes:
                if node.node_id not in seen_ids:
                    seen_ids.add(node.node_id)
                    all_nodes.append(node)

        english_query = search_queries[1] if len(search_queries) > 1 else query_text
        reranked_nodes = self.reranker.postprocess_nodes(all_nodes, query_str=english_query)

        context_str = "\n\n---\n\n".join([node.get_content() for node in reranked_nodes])

        qa_template_str = (
            "Eres un asistente tecnico experto. Se te proporcionan fragmentos de documentacion tecnica oficial.\n"
            "Analiza TODOS los fragmentos de contexto y sintetiza una respuesta completa y precisa.\n"
            "---------------------\n"
            f"{context_str}\n"
            "---------------------\n"
            f"Pregunta: {query_text}\n\n"
            "REGLAS ESTRICTAS:\n"
            "1. Responde SIEMPRE en espanol.\n"
            "2. Usa UNICAMENTE la informacion presente en el contexto anterior.\n"
            "3. NUNCA inventes, supongas ni agregues informacion que NO este en el contexto.\n"
            "4. Si el contexto contiene tablas, reproducelas completas y fielmente.\n"
            "5. Si la informacion esta repartida en varios fragmentos, combinalos en una respuesta coherente.\n"
            "6. Si el contexto NO contiene informacion suficiente para responder, di exactamente:\n"
            "   'No encontre informacion especifica sobre eso en los documentos cargados.'\n"
        )

        response = self.llm.complete(qa_template_str)
        final_response = str(response)

        sources = []
        for node in reranked_nodes:
            file_name = node.metadata.get("file_name", "Archivo desconocido")
            page = node.metadata.get("page_label", None)
            if page and page != "N/A":
                sources.append(f"{file_name} (Pag. {page})")
            else:
                sources.append(f"{file_name}")

        if sources:
            unique_sources = list(set(sources))
            final_response += "\n\n**Fuentes:**\n- " + "\n- ".join(unique_sources)

        return final_response

    def stream_query(self, query_text: str):
        """Generates a stream of events and content for the chat UI."""
        yield {"event": "thinking", "data": "Analizando tu pregunta..."}
        
        if not self.index:
            self.index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                embed_model=self.embed_model
            )

        yield {"event": "thinking", "data": "Optimizando búsqueda..."}
        search_queries = self._rewrite_query(query_text, self.llm)

        yield {"event": "thinking", "data": "Consultando base de conocimiento vectorizada..."}
        retriever = self.index.as_retriever(similarity_top_k=5)
        all_nodes = []
        seen_ids = set()
        for sq in search_queries:
            nodes = retriever.retrieve(sq)
            for node in nodes:
                if node.node_id not in seen_ids:
                    seen_ids.add(node.node_id)
                    all_nodes.append(node)

        english_query = search_queries[1] if len(search_queries) > 1 else query_text
        reranked_nodes = self.reranker.postprocess_nodes(all_nodes, query_str=english_query)

        yield {"event": "thinking", "data": f"Leyendo {len(reranked_nodes)} fragmentos relevantes..."}
        context_str = "\n\n---\n\n".join([node.get_content() for node in reranked_nodes])

        qa_template_str = (
            "Eres un asistente tecnico experto. Se te proporcionan fragmentos de documentacion tecnica oficial.\n"
            "Analiza TODOS los fragmentos de contexto y sintetiza una respuesta completa y precisa.\n"
            "---------------------\n"
            f"{context_str}\n"
            "---------------------\n"
            f"Pregunta: {query_text}\n\n"
            "REGLAS ESTRICTAS:\n"
            "1. Responde SIEMPRE en espanol.\n"
            "2. Usa UNICAMENTE la informacion presente en el contexto anterior.\n"
            "3. NUNCA inventes, supongas ni agregues informacion que NO este en el contexto.\n"
            "4. Si el contexto contiene tablas, reproducelas completas y fielmente usando Markdown.\n"
            "5. Usa bloques de codigo para comandos y configuraciones.\n"
            "6. Si la informacion esta repartida en varios fragmentos, combinalos en una respuesta coherente.\n"
            "7. Si el contexto NO contiene informacion suficiente para responder, di exactamente:\n"
            "   'No encontre informacion especifica sobre eso en los documentos cargados.'\n"
        )

        response_gen = self.llm.stream_complete(qa_template_str)
        
        for delta in response_gen:
            yield {"event": "message", "data": delta.delta}

        sources = []
        for node in reranked_nodes:
            file_name = node.metadata.get("file_name", "Archivo desconocido")
            page = node.metadata.get("page_label", None)
            if page and page != "N/A":
                sources.append(f"{file_name} (Pag. {page})")
            else:
                sources.append(f"{file_name}")

        if sources:
            unique_sources = list(set(sources))
            sources_text = "\n\n**Fuentes:**\n- " + "\n- ".join(unique_sources)
            yield {"event": "message", "data": sources_text}
        
        yield {"event": "done", "data": ""}



try:
    kb = VectorKnowledgeBase()
except Exception as e:
    print(f"[ADVERTENCIA] No se pudo inicializar la base de conocimiento: {e}")
    kb = None

# from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from langchain_core.embeddings import Embeddings
from langchain_huggingface.embeddings import HuggingFaceEmbeddings  # For downloading and using embedding model locally
from langchain_experimental.text_splitter import SemanticChunker
import multiprocessing as mp

import torch




def semantic_chunker(document: list[str],model:str):
    model_kwargs = {'device': 'mps'}
    local_embedder = HuggingFaceEmbeddings(
        model_name=model,
        cache_folder="/Users/prashantgurung/.cache/huggingface/hub", # NOTE: CHANGE THIS ACCORDINGLY
        model_kwargs=model_kwargs
    )
    chunker = SemanticChunker(local_embedder)
    chunk_received = chunker.create_documents(document)
    return chunk_received # returns List[Document]

# For multiprocessing and getting the results back
def semantic_chunker_mp(document: list[str],model:str,queue:mp.Queue):
    model_kwargs = {'device': 'mps'}
    local_embedder = HuggingFaceEmbeddings(
        model_name=model,
        cache_folder="/Users/prashantgurung/.cache/huggingface/hub", # NOTE: CHANGE THIS ACCORDINGLY
        model_kwargs=model_kwargs
    )
    chunker = SemanticChunker(local_embedder)
    chunk_received = chunker.create_documents(document)
    queue.put(chunk_received)

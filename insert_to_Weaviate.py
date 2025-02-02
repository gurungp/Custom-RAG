import weaviate
import weaviate.classes as wvc
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def vectorize_and_insert(collection_name:str,inference_url:str,data: list[Document]):
    try: 
        client = weaviate.connect_to_local()
        assert client.is_live()
        print("Client is live")

        # Create collection if it doesn't already exist
        existing_collections = client.collections.list_all()
        if collection_name in existing_collections:
            print(f"Collection {collection_name} exists")
        else:
            collection = client.collections.create(
                name=collection_name,
                vectorizer_config=[
                    wvc.config.Configure.NamedVectors.text2vec_transformers(
                        name="content_vec",
                        source_properties=["content"],
                        inference_url=inference_url
                    )
                ],
                properties=[
                    wvc.config.Property(
                        name="content",
                        data_type=wvc.config.DataType.TEXT
                    )
                ]
            )

        #Insert Data
        collection = client.collections.get(collection_name)
        with collection.batch.dynamic() as batch:
            for section in data:
                collection_obj = {
                    "content": section.page_content
                }
                batch.add_object(
                    properties=collection_obj
                )
    finally:
        print("Closing Client")
        client.close()

# Custom method to store image, modify according to needs/attributes or add another similar methods
def store_without_vectorizing(collection_name:str,data: list):
    try: 
        client = weaviate.connect_to_local()
        assert client.is_live()
        print("Client is live")

        # Create collection if it doesn't already exist
        existing_collections = client.collections.list_all()
        if collection_name in existing_collections:
            print(f"Collection {collection_name} exists")
        else:
            collection = client.collections.create(
                name=collection_name,
                properties=[
                    wvc.config.Property(name="uuid",data_type=wvc.config.DataType.UUID,skip_vectorization=True),
                    wvc.config.Property(name="pg_no",data_type=wvc.config.DataType.TEXT,skip_vectorization=True),
                    wvc.config.Property(name="b64",data_type=wvc.config.DataType.TEXT,skip_vectorization=True),
                    wvc.config.Property(name="bounding_box",data_type=wvc.config.DataType.TEXT,skip_vectorization=True),
                ]
            )

        #Insert Data
        collection = client.collections.get(collection_name)
        collection.data.insert_many(data)
        
    finally:
        print("Closing Client")
        client.close()

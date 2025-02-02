import shutil
import tkinter as tk

import weaviate
import weaviate.classes.config as wc
import weaviate.classes.query as wq
import os
import multiprocessing as mp

 
session_chunks = [] # All the retrieved chunks of this session


def get_all_collections():
    print("Printing all collections")
    client = weaviate.connect_to_local()
    collectionItem = client.collections.list_all()
    for key,value in collectionItem.items():
        print(key)
    client.close()


def query(collection_name:str,prompt:str,limit:int):
    # Name of the collection/database from where to query from
    client = weaviate.connect_to_local()
    collection = client.collections.get(collection_name)
    prompt_result = collection.query.near_text(prompt,limit=limit)
    for result in prompt_result.objects:
        session_chunks.append(result.properties['content'])
    client.close()
    query_llm(prompt=prompt)
    return prompt_result

def query_llm(prompt:str):# Code to use the llm of choice  
    # Use session_chunks to feed the chunks received from database as RAG
    print("LLM TASKS")
    print(session_chunks)
    print(f"Length of session_chunks: {len(session_chunks)}")
    ask_for_query()

def delete_collection(collection_name:str):
    client =  weaviate.connect_to_local()
    client.collections.delete(collection_name)
    client.close()


def delete_all_collection():
    client =  weaviate.connect_to_local()
    client.collections.delete_all()
    client.close()

def ask_for_query():
    user_question = input("Query: ")
    if(user_question=="QUIT"):
        return
    else:
        query(collection_name="Maths_PreCalc_1",prompt=user_question,limit=3)
        
ask_for_query()

# r1 = query("Maths_PreCalc_1","How to calculate distance between two points",limit=4)
# r2 = query("Maths_PreCalc_2","How to calculate distance between two points",limit=4)

# print(r1)
# print(r2)

# delete_all_collection()
# get_all_collections()

# Deepseek/Other LLM intregation
# Get prompt from user and send it to query database.
# Get the chunks and feed it to deepseek with the question


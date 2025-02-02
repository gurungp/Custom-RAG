# Sending the pdf page to the llamaparse api
# 

import nest_asyncio
import os
from llama_parse import LlamaParse
from pprint import pprint
from openai import OpenAI
from unstructered_operations import get_pg_num_from_file_name
from config import GlobalVars

nest_asyncio.apply()

# TODO: Cycle between api keys to reduce usage of each account

llama_api_key1 = os.getenv("LLAMA_CLOUD_API_KEY")
llama_api_key2 = os.getenv("LLAMA_CLOUD_API_KEY2")
llama_api_key3 = os.getenv("LLAMA_CLOUD_API_KEY3")
llama_api_key4 = os.getenv("LLAMA_CLOUD_API_KEY4")
llama_api_key5 = os.getenv("LLAMA_CLOUD_API_KEY5")
llama_api_key6 = os.getenv("LLAMA_CLOUD_API_KEY6")

# openaikey = os.getenv("OPEN_ROUTER_API_KEY")
# githubtoken = os.getenv("GITHUB_TOKEN_CURRENT")
# deepseekkey = os.getenv("DEEPSEEK_API_KEY")

list_llama_api_keys = []
list_llama_api_keys.append(llama_api_key1)
list_llama_api_keys.append(llama_api_key2)
list_llama_api_keys.append(llama_api_key3)
list_llama_api_keys.append(llama_api_key4)
list_llama_api_keys.append(llama_api_key5)
list_llama_api_keys.append(llama_api_key6)



def cycle_through_keys():
    GlobalVars.current_llama_api_index += 1
    if GlobalVars.current_llama_api_index>5:
        GlobalVars.current_llama_api_index = 0
    return GlobalVars.current_llama_api_index

def parse_with_llama(path_to_file:str,prompt:str) -> tuple:
    parsing_Instruction = prompt
    premium_mode = True
    print(f"Using llama_api_key indexed: {GlobalVars.current_llama_api_index}")

    parser = LlamaParse(
        api_key=list_llama_api_keys[GlobalVars.current_llama_api_index],  # can also be set in your env as LLAMA_CLOUD_API_KEY
        result_type="markdown",  # "markdown" and "text" are available
        num_workers=4,  # if multiple files passed, split in `num_workers` API calls
        verbose=True,
        language="en",  # Optionally you can define a language, default=en
        extract_charts=True,
        parsing_instruction=parsing_Instruction,
        premium_mode=premium_mode,
    )
    GlobalVars.current_llama_api_index = cycle_through_keys()
    documents = parser.load_data(path_to_file)
    if len(documents)>=1: # if its not empty
        return (documents[0].text,path_to_file)
    else:
        return None

# documents = parse_with_llama("/Users/prashantgurung/PycharmProjects/DocumentRag/Rag App/pg_2.pdf")

# print("Printing Document")
# print(documents[0][0].text)
# print(type(documents[0]))
# print("Printing Path")
# print(documents[1])
# print(type(documents[1]))
# print(len(documents[1]))
# print(len(documents[0]))

# pprint(documents[0].text_resource.text)

    
    




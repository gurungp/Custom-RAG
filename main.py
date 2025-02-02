
import tkinter as tk
from tkinter import filedialog, StringVar
from async_tkinter_loop import async_handler,async_mainloop
import pickle
import time

from pathlib import Path
import llama_parse_pdf
import unstructered_operations
import match_image_with_markdown
from pdf_splitter import split_into_pages_range
from draw_bounding_box import draw_bounding_box
from langchain_core.documents import Document
from custom_chunker import semantic_chunker_mp,semantic_chunker
import os
import pandas as pd
from insert_to_Weaviate import vectorize_and_insert, store_without_vectorizing
import uuid
import shutil
import multiprocessing as mp
import concurrent.futures
from config import GlobalVars


# HELPER FUNCTIONS
def flatten_list(lst: list) -> list:
    flattened_list = []
    for sublist in lst:
        if isinstance(sublist[0],list):
            flatten_list(sublist)
        else:
            for elements in sublist:
                flattened_list.append(elements)
    return flattened_list

def extract_number(filename):
    if not filename.startswith('.'):
        page_num = unstructered_operations.get_pg_num_from_file_name(filename=filename)
        #print(f"extract_number : page_num {page_num}" )
        return int(page_num) if page_num else 0
    else:
        return 0


# region RAG APP FUNCTIONS START

# STEP 1 : Split the provided pdf into individual pages
temp_dir_pdf_files = "/Temp_Pdf_Folder"
# cur_dir = str(os.getcwd())
# path_to_pdf = f'{cur_dir}/Rag App/Precalc Pearson/37-39.pdf'

# STEP 2: Now provide each of those files to Llama Parse and store the result

def parse_with_llama(output_dir_of_single_pages:str,output_dir:str,prompt:str,page_from:int,page_to:int):
    parsed_documents = [] 
    for dirpath, dirnames,filenames in os.walk(output_dir_of_single_pages):
        for filename in sorted(filenames,key=extract_number):
            if not filename.startswith('.'): # Exclude hidden files as it starts with '.' in MacOS
                full_path = output_dir_of_single_pages + f"/{filename}"
                print("File: " , full_path)
                result = llama_parse_pdf.parse_with_llama(path_to_file=full_path,prompt=prompt)
                if result!=None:
                    parsed_documents.append(result)

    # Save the list of tuples("Text from the page", "path to the file which also has the pg_no")
    df = pd.DataFrame(parsed_documents, columns=['Content','Path'])
    df.to_csv(f"{output_dir}/markdown_with_llamaparse_{page_from}_to_{page_to}.csv")
    return parsed_documents


# STEP 3: Get the pictures from each page in base64 with unstructured. We also get its bounding box, uuid and page num in dict
# TODO: Save the data in a Weaviate database

def parse_with_unstructured(output_dir_of_single_pages:str,output_folder:str,page_from:int,page_to:int)->dict:
    parsed_with_unstructured = []
    parsed_with_unstructured_dict = {}
    for dirpath, dirnames,filenames in os.walk(output_dir_of_single_pages):
        for filename in filenames:
            if not filename.startswith('.'): # Exclude hidden files as it starts with '.' in MacOS
                full_path = output_dir_of_single_pages + f"/{filename}"
                print("File: " , full_path)
                # Now parse with unstructured. We list[dict] where dicts are b64,uuid,boundingbox,pg_no
                parsed_with_unstructured.append(unstructered_operations.parse_with_unstructured(full_path,output_dir=output_folder))

                if(len(parsed_with_unstructured)>=1): # if the list is not empty, we save it to disk in csv format
                    parsed_with_unstructured_dict = {item:dict_item[item] for dict_item in parsed_with_unstructured for item in dict_item}
                    for pg,value in parsed_with_unstructured_dict.items():
                        df = pd.DataFrame(value)
                        df.to_csv(f"{output_folder}/image_info_pg_{pg}.csv",index=False)
    # Sorting parsed_with_unstructured_dict
    sorted_parsed_with_unstructured_dict = sorted(parsed_with_unstructured_dict.items()) # this turns it into a list of tuple
    # Saving this as binary using pickle to easily get it back in same format when necessary
    with open(f'{output_folder}/image_info_pg_{page_from}_to_{page_to}.pkl','wb') as f:
        pickle.dump(sorted_parsed_with_unstructured_dict,f)

    return sorted_parsed_with_unstructured_dict

# STEP 4: Match the image of the page to the extracted markdown and place the uuid on the correct place of the text
        # to correctly render later or do other functions and output the final markdown te

def match_img_with_markdown(path_to_file_from_llamaparse: str,folder_of_unstructured:str,page_from:int,page_to:int)->list[str]:
    
    precheck()

    llama_parsed_file = Path(path_to_file_from_llamaparse)
    if not llama_parsed_file.is_file():
        start_parse_label.config(text="Output folder of llamaparse doesn't exist")
        return
    if folder_path_final_md.get()=="None":
        start_parse_label.config(text="Markdown output folder not found")
        return
    if folder_path_unstructured.get()=="None":
        start_parse_label.config(text="Unstructured output folder not found")
        return
# region BACK TO SORTED DICT IMAGE INFO FROM UNSTRUCTURED FROM CSV FILES
    """
    back_to_parsed_unstructure = []
    back_to_parsed_unstructure_dict = {}
    for dirpath, dirnames,filenames in os.walk(folder_of_unstructured):
        for filename in filenames:
            if not filename.startswith('.'): # Exclude hidden files as it starts with '.' in MacOS
                full_path = folder_of_unstructured + f"/{filename}"
                print("File: " , full_path)
                temp = pd.read_csv(full_path)
                for item in temp.iterrows():
                    dict_temp = {}
                    pg_no = (item[1]['pg_no'])
                    uuid_var = uuid.UUID((item[1]['uuid']))
                    boundingbox= (item[1]['bounding_box']).apply(ast.literal_eval) # To parse the tuple back from the string stored in the CSV, 
                                                                                    # we can use Python's ast.literal_eval function. This safely evaluates 
                                                                                    # a string containing a valid Python expression (like your tuple) and 
                                                                                    # converts it back to its original type.
                    b64 = (item[1]['b64'])
                    dict_temp['uuid'] = uuid_var
                    dict_temp['pg_no'] = pg_no
                    dict_temp['bounding_box'] = boundingbox
                    dict_temp['b64'] = b64
                    
                    back_to_parsed_unstructure_dict.setdefault(pg_no,[]).append(dict_temp)
    sorted_back_to_parsed_with_unstructured_dict = sorted(back_to_parsed_unstructure_dict.items())
    print("PRINTING SORTED BACK TO PARSED DICT")
    print(sorted_back_to_parsed_with_unstructured_dict)
    """
# region End getting back 

    # Using pickle instead to get back the sorted dict image info from unstructured
    with open(f'{folder_of_unstructured}/image_info_pg_{page_from}_to_{page_to}.pkl','rb') as f:
        sorted_back_to_parsed_with_unstructured_dict = pickle.load(f)


    final_markdown_texts = []
    imported_df = pd.read_csv(f'{path_to_file_from_llamaparse}')
    parsed_documents = list(zip(imported_df["Content"],imported_df["Path"]))

    if(len(parsed_documents)<=0):
        print("Empty Parsed Contents from llamaparse")
        return None
    else:         
        for item in parsed_documents: # parsed_documents is a list of tuples
            md_text = item[0]  # the first part of tuple holds the parsed marked down text
            path_to_page = item[1] # the second part of tuple holds the path and pg no

            page_num = unstructered_operations.get_pg_num_from_file_name(path_to_page)
            # print(f"Type of page_num: {type(page_num)} , value: {page_num}")

            for tuple_item in sorted_back_to_parsed_with_unstructured_dict:
                # print(f"Type of tuple_item[0]: {type(tuple_item[0])} , value: {tuple_item[0]}")
                # print(f"Type of tuple_item[1]: {type(tuple_item[1])} , value: {tuple_item[1]}")
                if tuple_item[0]==page_num:
                    for item_list in tuple_item[1]:
                        bounding_box = [tpl for tpl in item_list['bounding_box']] # flattening the tuple of tuples
                        uuid_img = item_list['uuid']
                        prompt = f"This image is a page from Math text book. I have parsed the texts into a markdown format. The graphs and/or images arent parsed but are extracted separately with a unique-id. But in this image there is a red bounding box which represents the extracted image or graph. Now as you can see on the markdown text there are elements like [someText] and the someText can be anything like Figure 7 or any description of an image. Now carefully analyze the content inside the red bounding box and determine which [ someText ] element matches the content inside the red bounding box and then append the id with 'id={uuid_img}' and a description of the image inside the red bounding box as prefix, inside the same [ ], and the whole markdown text with the modification and rest as it is . Also dont give any explanation and reasons . And here is the Markdown text: {md_text}"
                        print(bounding_box)
                        print()
                        b64_with_bounding_box = draw_bounding_box(path_to_page,folder_path_image.get(),uuid_img,page_num,bounding_box)
                        # print(b64_with_bounding_box)
                        md_text = match_image_with_markdown.markdown_wrt_image(markdown=md_text,b64_img=b64_with_bounding_box,prompt=prompt)
            final_markdown_texts.append(md_text)
        GlobalVars.final_markdown_texts =  final_markdown_texts

        # Output the file in the directory chosen
        final_string = ""
        for text in final_markdown_texts:
            final_string += text

        # NOTE: Final name should reflect its content such as from page x to y
        #       and should be changed to appropriate name every run 
        with open(f"{folder_path_final_md.get()}/{f"final_markdown_{GlobalVars.page_from}_to_{GlobalVars.page_to}.md"}",'w',encoding='utf-8') as file: 
            file.write(final_string)
        start_parse_label.config(text="Finished matching image with content and storing the final markdown text")

        # LOOP ACCORDING TO PAGES . 1 get page num from second part of tuple of parsed_documents
                                #   2 then go through every parsed_with_unstructured_dict and where pg_no is equal to it
                                #     get the b64 of the extracted image

# Custom function to insert images with its info such as uuid, bounding box, b64 and pg_no
def store_image_info(input_dir:str,collection_name:str):
    # Get all the csv files from the folder
    # Turn them into dict or list of dicts
    # insert into database
    final_list_data = []
    for dirpath, dirnames,filenames in os.walk(input_dir):
        for filename in filenames:
            if filename.endswith(".csv"):
                full_path = input_dir + f"/{filename}"
                img_desc = pd.read_csv(full_path)

                for i in range(len(img_desc)):
                    data = img_desc.iloc[i].to_dict()
                    temp_dict = {}
                    temp_dict['uuid'] = uuid.UUID(data['uuid'])
                    temp_dict['pg_no'] = str(data['pg_no'])
                    temp_dict['b64'] = data['b64']
                    temp_dict['bounding_box'] = data['bounding_box']
                    print(type(temp_dict['uuid']))
                    final_list_data.append(temp_dict)
    store_without_vectorizing(collection_name=collection_name,data=final_list_data)

def vectorize_then_insert(path_to_md_file:str):
    
    if(file_path_final_md.get()=="None"):
        start_parse_label.config(text="Please select the mark down file output from step 10")
        return
    if(folder_path_main.get()=="None"):
        start_parse_label.config(text="Please select Main Folder")
        return
    
    print("\n SEMANTIC CHUNKING\n")

    start_parse_label.config(text="SEMANTIC CHUNKING...")
    with open(path_to_md_file,"r") as file:
        md_text = file.read()


    md_text_list = []
    md_text_list.append(md_text)
    # print(f"md_text : {md_text_list}")
    # print(f"{type(md_text_list)}")

    # Chunk the text 

    # chunk_received1 = semantic_chunker(md_text_list,model="WhereIsAI/UAE-Large-V1")
    # chunk_received2 = semantic_chunker(md_text_list,model="BAAI/bge-large-en-v1.5")

    start = time.time()

    chunk_received1 = semantic_chunker(md_text_list,"sentence-transformers/all-MiniLM-L6-v2")
  
    # q1 = mp.Queue()
    # q2 = mp.Queue()

    # process_chunker1 = mp.Process(target=semantic_chunker_mp,args=(md_text_list,"WhereIsAI/UAE-Large-V1",q1))
    # process_chunker2 = mp.Process(target=semantic_chunker_mp,args=(md_text_list,"BAAI/bge-large-en-v1.5",q2))

    # process_chunker1.start()
    # process_chunker2.start()

    # process_chunker1.join()
    # process_chunker2.join()

    # chunk_received1 = q1.get()
    # chunk_received2 = q2.get()
    end = time.time()


    print(f"Total time to Chunk with all-MiniLM-L6-v2: {end-start} \n")


    start = time.time()

    chunk_received2 = semantic_chunker(md_text_list,"BAAI/bge-large-en-v1.5")
    end = time.time()


    print(f"Total time to Chunk with BAAI/bge-large-en-v1.5: {end-start} \n")
    # Edit the collection names according to the book or content (two not necessary)

    collection_name1 = "Maths_PreCalc_1"
    collection_name2 = "Maths_PreCalc_2"
  
   
    # Inserting into Weaviate.
    # Make sure Weaviate and t2v-transformer instance according to the transformer model and its url are running
    start_parse_label.config(text="INSERTING INTO WEAVIATE...")

    start = time.time()

    vectorize_and_insert(collection_name1,"http://t2v-transformers-miniLM-L6-v2:8080",chunk_received1)
    vectorize_and_insert(collection_name2,"http://t2v-transformers3-baai-bge-large-1.5:8081",chunk_received2)


    # process_vectorize1 = mp.Process(target=vectorize_and_insert,
    #                                 args=(collection_name1,"http://t2v-transformers-miniLM-L6-v2:8080",
    #                                       chunk_received1))
    # process_vectorize2 = mp.Process(target=vectorize_and_insert,
    #                                 args=(collection_name2,"http://t2v-transformers3-baai-bge-large-1.5:8081",
    #                                 chunk_received2))
    # process_vectorize1.start()
    # process_vectorize2.start()
    # process_vectorize1.join()
    # process_vectorize2.join()

    end = time.time()

    print(f"Time taken to vectorize is {end-start}")
   

    # This step is not necessary and can be modified according the querying needs
    print("STORING IMAGES INFO")
    start_parse_label.config(text="STORING IMAGES INFO...")
    img_collection_name1 = collection_name1 + "_images"
    img_collection_name2 = collection_name2 + "_images"


    start = time.time()
    store_image_info(folder_path_unstructured.get(),img_collection_name1)
    store_image_info(folder_path_unstructured.get(),img_collection_name2)
    # process_store1 = mp.Process(target=store_image_info,args=(folder_path_image.get(),img_collection_name1))
    # process_store2 = mp.Process(target=store_image_info,args=(folder_path_image.get(),img_collection_name2))
    # process_store1.start()
    # process_store2.start()
    # process_store1.join()
    # process_store2.join()

    end = time.time()
    print(f"Time taken to Insert Image is {end-start}")
    start_parse_label.config(text="FINISHED STORING IMAGES INFO")




# RAG APP FUNCTIONS END
# endregion
    
# Functions to check every paths and folders that needs to be set before parsing using Llama Parse and Unstructured
def precheck():
    if(file_path_1.get()=="None"):
        start_parse_label.config(text="Select the File First in Step 1")
        return False

    page_from = pages_from_entry.get()
    page_to = pages_to_entry.get()


    print(pages_from_entry.get().isdigit())
    if(page_from.isdigit() and page_to.isdigit()):
        page_from = int(page_from)
        page_to = int(page_to)
        GlobalVars.page_from = page_from
        GlobalVars.page_to = page_to
        if(page_from>page_to):
            start_parse_label.config(text="Invalid Range")
            return False
    
    else:
        start_parse_label.config(text="Invalid input. Put numbers only")
        return False
    if(not folder_path_main.get()):
        start_parse_label.config(text="Main folder not set")
        return False
    if(not prefix_box.get()):
        start_parse_label.config(text="Fill in the prefix in Step 3")
        return False
    if(folder_path_llamaparse.get()=="None"):
        start_parse_label.config(text="Select the main output folder first")
        return False
    if(folder_path_unstructured.get()=="None"):
        start_parse_label.config(text="Select the main output folder first")
        return False
    if(folder_path_final_md.get()=="None"):
        start_parse_label.config(text="Select the main output folder first")
        return False
    if(folder_path_image.get()=="None"):
        start_parse_label.config(text="Select the main output folder first")
        return False

# Split PDF and Parse with Llamaparse and unstructured and output files
def start_parse():

    if(precheck()==False):
        return

    start_parse_label.config(text="Splitting PDF ..... ")
 
    print(f"Prefix {prefix_box.get()}")
    print(f"Llamaparse output dir: {folder_path_llamaparse.get()}")
    print(f"Unstructured output dir: {folder_path_unstructured.get()}")
    print(f"Final markdown output dir: {folder_path_final_md.get()}")
    print(f"Final images output dir: {folder_path_image.get()}")


    output_pdf_folder = folder_path_main.get()+temp_dir_pdf_files
    split_into_pages_range(file_path_1.get(),output_pdf_folder,prefix_box.get(),GlobalVars.page_from,GlobalVars.page_to)

    # prompt = """The page may contain two columns like that of a scientific paper. Convert any and every math equations into LATEX format (between $$) and Describe any Graphs,pictures,images and figures and Strictly put it (between [])  """.strip()
    
    process_llamaParse = mp.Process(target=parse_with_llama,
                                    args=(output_pdf_folder,folder_path_llamaparse.get(),GlobalVars.prompt_llamaparse,GlobalVars.page_from,GlobalVars.page_to))
    process_unstructure_parse = mp.Process(target=parse_with_unstructured,
                                           args=(output_pdf_folder,folder_path_unstructured.get(),GlobalVars.page_from,GlobalVars.page_to))
    process_llamaParse.start()
    process_unstructure_parse.start()
    process_llamaParse.join()
    process_unstructure_parse.join()
    start_parse_label.config(text="Parsing finished by Llama Parse and Unstructured")
    # parsed_documents_with_llama = parse_with_llama(temp_dir_pdf_files,folder_path_1.get(),prompt)
    # parse_with_unstructured(temp_dir_pdf_files)


# region GUI Related Functions to get the texts from the buttons and text boxes

def select_file():
    file_path = filedialog.askopenfilename(
            title="Select a file",
            filetypes=(("All Files", "*.*"), ("PDF Files", "*.pdf")),
            initialdir="/"  # Start from root directory
    )
    print(f"File path from select_file : {file_path}")
    if file_path:
        file_select_label_1.config(text=file_path)
        file_path_1.set(file_path)
    else:
        file_select_label_1.config(text="Invalid path to file")
        file_path_1.set("None")

def select_markdown_file():
    file_path = filedialog.askopenfilename(
            title="Select a file",
            filetypes=(("All Files", "*.*"), ("Markdown Files", "*.md")),
            initialdir="/"  # Start from root directory
    )
    print(f"File path from select_file : {file_path}")
    if file_path:
        select_markdown_file_label.config(text=file_path)
        file_path_final_md.set(file_path)
    else:
        select_markdown_file_label.config(text="Invalid path to file")
        file_path_final_md.set("None")

def select_folder_main_out_dir():
    folder_path = filedialog.askdirectory(
        title="Select a folder",
        initialdir="/"  # Start from root directory
    )
    
    if folder_path:
        folder_path_main.set(folder_path)
        print(folder_path)
        llamaparse_folder_path = folder_path + "/llamaparse output"
        unstructured_folder_path = folder_path + "/unstructured output"    
        final_markdown_folder_path = folder_path + "/final markdown output"        
        image_folder_path = folder_path + "/image output"
        Temp_pdf_folder = folder_path + temp_dir_pdf_files        
        print(llamaparse_folder_path)

        if(os.path.exists(llamaparse_folder_path)):
            shutil.rmtree(llamaparse_folder_path)
        if(os.path.exists(unstructured_folder_path)):
            shutil.rmtree(unstructured_folder_path)
        if(os.path.exists(final_markdown_folder_path)):
            shutil.rmtree(final_markdown_folder_path)
        if(os.path.exists(image_folder_path)):
            shutil.rmtree(image_folder_path)
        if(os.path.exists(Temp_pdf_folder)):
            shutil.rmtree(Temp_pdf_folder)


        folder_path_llamaparse.set(llamaparse_folder_path)
        folder_path_unstructured.set(unstructured_folder_path)
        folder_path_final_md.set(final_markdown_folder_path)
        folder_path_image.set(image_folder_path)
        folder_path_pdf_files.set(Temp_pdf_folder)

        os.mkdir(llamaparse_folder_path)
        os.mkdir(unstructured_folder_path)
        os.mkdir(final_markdown_folder_path)
        os.mkdir(image_folder_path)
        os.mkdir(Temp_pdf_folder)

        set_main_folder_label.config(text=folder_path)
    else:
        set_main_folder_label.config(text="Folder path not selected")
        folder_path_main.set("None")



# endregion

if __name__ == "__main__":
    # Main Window
    root = tk.Tk()
    root.title("Rag App")
    root.geometry("1200x600")  # Window size
    root.iconbitmap("./ragappicon.ico")
    
    # Grid layout of the main window
    root.grid_rowconfigure(0,weight=1) # Top row
    root.grid_rowconfigure(1, weight=0) # Bottom row
    root.grid_columnconfigure(0,weight=1)
    root.grid_columnconfigure(1, weight=1)


    # Create UI sections
    div1 = tk.Frame(root, bg="lightblue", width=445, height=395)
    div2 = tk.Frame(root, bg="lightgreen", width=445, height=395)
    bottom_div = tk.Frame(root, bg="lightgray", width=895, height=200)
    
    div1.grid(row=0, column=0,sticky="nsew")
    div2.grid(row=0, column=1,sticky="nsew")
    bottom_div.grid(row=1, column=0, columnspan=2, sticky="nsew")
    
    # Configure grid layout for sections to expand properly
    div1.grid_propagate(False)
    div2.grid_propagate(False)
    bottom_div.grid_propagate(False)


    # Text box to show page range
    range_select_from = tk.Label(div1,text="2. Parse pages from")
    range_select_to = tk.Label(div1,text="to")
    # Entry box to input pages from and to
    pages_from_entry = tk.Entry(div1,width=3)
    pages_to_entry = tk.Entry(div1,width=3)

    range_select_from.pack(padx=1,pady=1)
    pages_from_entry.pack(padx=1,pady=1)
    range_select_to.pack(padx=1,pady=1)
    pages_to_entry.pack(padx=1,pady=1)

    # Prefix for splitted pdf files
    prefix_label = tk.Label(div1,text="3. Prefix")
    prefix_box = tk.Entry(div1,width=3)
    prefix_label.pack(padx=1,pady=3)
    prefix_box.pack(padx=1,pady=3)

      
    # File select for paring
    file_path_1 = StringVar()
    file_path_1.set("None")
    file_select_button = tk.Button(div1, bg="white" ,text="1. File Select", command=select_file)
    file_select_button.pack(pady=2,padx=5)


    file_select_label_1 = tk.Label(div1, text="File Not Selected Yet",wraplength=350)
    file_select_label_1.pack(pady=5)


    # Main folder
    folder_path_main = StringVar()
    folder_path_main.set("None")
    set_main_folder = tk.Button(div1, 
                            bg="white" ,
                            text="Set main folder",
                            command=select_folder_main_out_dir)
    set_main_folder.pack(pady=15,padx=5)
    set_main_folder_label = tk.Label(div1, text="",wraplength=350)
    set_main_folder_label.pack(pady=5)

    # Llama parse output directory

    folder_path_llamaparse = StringVar()
    folder_path_llamaparse.set("None")


    # Output dir of Unstructured results
    folder_path_unstructured = StringVar()
    folder_path_unstructured.set("None")


    # Output dir of Final markdown
    folder_path_final_md = StringVar()
    folder_path_final_md.set("None") 

    # Parse with LlamaParse and Unstructured
    folder_path_image = StringVar()
    folder_path_image.set("None") 
    
    # Folder path for splitted pdf files
    folder_path_pdf_files = StringVar()
    folder_path_pdf_files.set("None")

    # Start Parse Button and Bottom Label
    start_parse = tk.Button(div2, 
                            bg="white" ,
                            text="Start Parse",
                            command=start_parse)
    start_parse.pack(pady=15,padx=5)
    start_parse_label = tk.Label(bottom_div, text="No Action Called",wraplength=350,height=10)
    start_parse_label.pack(pady=5)

    
    # Start matching markdown to images
    start_matching = tk.Button(div2, 
                            bg="white" ,
                            text="9. Start Matching",
                            command=lambda: match_img_with_markdown(f"{folder_path_llamaparse.get()}/markdown_with_llamaparse_{GlobalVars.page_from}_to_{GlobalVars.page_to}.csv",
                                                                    folder_path_unstructured.get(),GlobalVars.page_from,GlobalVars.page_to))
    start_matching.pack(pady=5)
    

    # Final markdown file select for inserting into Weaviate
    file_path_final_md = StringVar()
    file_path_final_md.set("None")

    # Choose the final markdown file
    choose_markdown_file = tk.Button(div2, 
                            bg="white" ,
                            text="Select Markdown file",
                            command=select_markdown_file)
    choose_markdown_file.pack(pady=15,padx=5)
    select_markdown_file_label = tk.Label(div2, text="",wraplength=350,)
    select_markdown_file_label.pack(pady=5)


     # Start matching markdown to images
    start_inserting = tk.Button(div2, 
                            bg="white" ,
                            text="11. Start Inserting",
                            command=lambda: vectorize_then_insert(file_path_final_md.get()))
    start_inserting.pack(pady=5)

    root.mainloop()
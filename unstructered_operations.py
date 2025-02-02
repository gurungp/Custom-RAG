from unstructured.partition.pdf import partition_pdf
from unstructured.partition.auto import partition
from unstructured.documents.coordinates import PixelSpace,RelativeCoordinateSystem
from pypdf import PdfWriter, PdfReader


import unstructured
import uuid


def get_pg_num_from_file_name(filename:str):
    last_underscore = filename.rfind('_')
    str_after_underscore = filename[last_underscore+1:].strip(".pdf")
    return str_after_underscore


def parse_with_unstructured(path_to_file:str,output_dir:str) -> list[dict]:
    elements = partition_pdf(
        filename=path_to_file,
        strategy="hi_res",
        infer_table_structure=True,
        extract_image_block_types=["Image","Table"], # Extract Images and tables as images
        # extract_image_block_output_dir=output_path,
        extract_image_block_to_payload=True,   # if true, will extract base64 for API usage and the images won't be output into the output dir
                                            # because it will generate base64 instead
        bounding_box=True,
        )

    list_page_dict = {}
    page_num = get_pg_num_from_file_name(path_to_file)
    for i,element in enumerate(elements):
         # To check where are the Images Elements and execute only if image elements exists
        if(isinstance(element,unstructured.documents.elements.Image)):
            print(f"{i} : {type(element)}")
            img_b64 = elements[i].metadata.image_base64
            bounding_box = elements[i].metadata.coordinates.points

            page_dict = {}
            page_dict['uuid'] = uuid.uuid4()
            page_dict['pg_no'] = page_num
            page_dict['bounding_box'] = bounding_box
            page_dict['b64'] = img_b64
            
            list_page_dict.setdefault(page_num,[]).append(page_dict)
            """
                Explanation:

                setdefault() Method:

                list_page_dict.setdefault(key, default) checks if key exists in the dictionary.
                If it doesn't exist, it initializes it with the default value (e.g., an empty list []).
                This ensures you don't have to manually check and initialize lists for each key.
                Appending Items:

                After ensuring that list_page_dict[key] is a list, you can directly use .append() to add items.
            """
    
    return list_page_dict


    


    



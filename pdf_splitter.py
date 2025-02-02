# Split all the pdf pages to single pages in a folder with specific naming convention
import os.path
from pypdf import PdfWriter,PdfReader


def split_into_pages(path_to_file:str,output_dir:str,pg_name_prefix:str,page_num_offset:int):
    if not os.path.isfile(path_to_file):
        print(f"The file {path_to_file} doesn't exists.")
    else:
        inputPdf = PdfReader(open(path_to_file,"rb"))
        numPages = inputPdf.get_num_pages()

        # Make output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Loop through all pages and output page one by one
        for i in range(numPages):
            output = PdfWriter()
            output.add_page(inputPdf.get_page(i))

            output_name = os.path.join(output_dir,f"{pg_name_prefix}_{i+page_num_offset}.pdf")
            print(output_name)
            with open(output_name,'wb') as file:
                output.write(file)

def split_into_pages_range(path_to_file:str,output_dir:str,pg_name_prefix:str,page_from:int,page_to:int):
    if not os.path.isfile(path_to_file):
        print(f"The file {path_to_file} doesn't exists.")
    else:
        inputPdf = PdfReader(open(path_to_file,"rb"))
        numPages = inputPdf.get_num_pages()

        # Loop through all pages and output page one by one
        if(page_from<=0 or page_to>numPages):
            print("Invalid page range given")
        else:
            for i in range(page_from,page_to+1):
                output = PdfWriter()
                output.add_page(inputPdf.get_page(i-1))

                output_name = os.path.join(output_dir,f"{pg_name_prefix}_{i}.pdf")
                print(output_name)
                with open(output_name,'wb') as file:
                    output.write(file)
# split_into_pages("/Users/prashantgurung/PycharmProjects/DocumentRag/purchase_order_document.pdf","test","pdfFile_test")

        
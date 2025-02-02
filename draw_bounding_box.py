import fitz
import base64
from PIL import Image, ImageDraw
from io import BytesIO


#  Draw the red bounding box of the image extracted on the whole pdf and get the b64 version  
def draw_bounding_box(pdfpath:str,output_path:str,uuid:str,page_num:str,coordinates:list,dpi:int=200) -> str:
    """
    Draws a bounding box on the specified page and location in the PDF
    """
    # Load the PDF as an image
    doc = fitz.open(pdfpath)
    page = doc.load_page(0) # Since we only provide one page at a time and its 0th indexed
    #pg_width,pg_height = elements[1].metadata.coordinates.system.width, elements[1].metadata.coordinates.system.height

    pix = page.get_pixmap(dpi=dpi) 

    #Convert Pixmap to an image
    img = Image.frombytes("RGB", [pix.width,pix.height],pix.samples)
    print(f"Width : {pix.width} , Height: {pix.height}")

 
    # Draw the bounding box
    draw = ImageDraw.Draw(img)
    draw.polygon(coordinates, outline="red", width=2)
    # pix.save(f"{output_path}/{uuid}_page_{page_num}.png")

    # Convert to PNG
    img.save(f"{output_path}/{uuid}_page_{page_num}.png","PNG")

    # Generate base64 of the modified image
    buffered = BytesIO()
    img.save(buffered,format="PNG")
    base64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return base64_img
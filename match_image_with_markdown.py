import google.generativeai as genai
import os



# We are using Gemini to do this but we can use any other ways that can accept images
def markdown_wrt_image(markdown:str,prompt:str,b64_img:str)->str: 
    # gemini-2.0-flash-exp
    # gemini-1.5-flash-8b
    gemini_api_key = os.getenv("GOOGLE_GEMINI_API")
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("models/gemini-2.0-flash-exp")
    response = model.generate_content([{'mime_type':'image/jpeg', 'data': b64_img}, prompt])
    return response.text

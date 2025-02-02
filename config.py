class GlobalVars:
    current_llama_api_index = 0
    page_from:int = 0
    page_to:int = 0
    final_markdown_texts = []
    prompt_llamaparse = """The page may contain two columns like that of a scientific paper. Convert any and every math equations into LATEX format (between $$) and Describe any Graphs,pictures,images and figures and Strictly put it (between [])  """.strip()

# Custom-RAG
A custom RAG app to vectorize information from pdf book such as Maths, Science or any other text books so that Relevant information can be fetched and put into the LLM of choice to learn faster

## Some Notes
1. Used Tkinter for GUI
2. LlamaParse is used for PDF parsing
3. Since, it doesn't get the pictures , Unstructured Open source is used to extract graphs, images etc
4. Then, multimodal llm (gemini in my case) is used to match the extracted image to where it belongs in text and given a uuid, so that we can recreate the context to the llm which we will be quering from and ask questions related to it.
5. Weaviate is used for the database.
6. Used custom inference model(s) to do semantic chunking.
7. For vectorization in Weaviate, again custom llm is used locally. (See t2v-inference on weaviate for more information)
8. So, docker can be used to host Weaviate and the t2v-inference.

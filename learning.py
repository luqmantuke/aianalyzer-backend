from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
import os
import PyPDF2

pdf_file_obj = open("2023_GPT4All_Technical_Report.pdf", "rb")
pdf_reader = PyPDF2.PdfReader(pdf_file_obj)
num_pages = len(pdf_reader.pages)
detected_text = ""

for page_num in range(num_pages):
    page_obj = pdf_reader.pages[page_num]
    detected_text += page_obj.extract_text() + "\n\n"

pdf_file_obj.close()

os.environ["OPENAI_API_KEY"] = "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"

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.create_documents([detected_text])

directory = "index_store"
vector_index = FAISS.from_documents(texts, OpenAIEmbeddings())
vector_index.save_local(directory)

vector_index = FAISS.load_local("index_store", OpenAIEmbeddings())
retriever = vector_index.as_retriever(search_type="similarity", search_kwargs={"k": 6})
conv_interface = ConversationalRetrievalChain.from_llm(ChatOpenAI(temperature=0), retriever=retriever)

chat_history = []


while True:
    query = input("You: ")
    result = conv_interface({"question": query, "chat_history": chat_history})
    chat_history.append((query, result["answer"]))
    print(chat_history)
    print(result["answer"])

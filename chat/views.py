import json
import uuid

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
import os
from aianalyzer import settings
from .models import *
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain.document_loaders import PyMuPDFLoader
from tempfile import NamedTemporaryFile

from .serializers import ChatHistorySerializer


@csrf_exempt
def ask_pdf(request):
    # try:

    pdf_file_obj = request.FILES['pdfFile']
    query = request.POST.get("query")
    user_id = request.POST.get("user_id")
    # Create a temporary file to save the uploaded PDF
    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf_file:
        # Write the content of the uploaded file to the temporary file
        for chunk in pdf_file_obj.chunks():
            temp_pdf_file.write(chunk)
    # Get the path to the temporary PDF file
    pdf_path = temp_pdf_file.name

    loader = PyMuPDFLoader(pdf_path)
    documents = loader.load()

    context_id = str(uuid.uuid4())

    os.environ["OPENAI_API_KEY"] = settings.OPEN_AI_KEY

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    directory =  settings.STATIC_ROOT
    vector_index = FAISS.from_documents(texts, OpenAIEmbeddings())
    vector_index.save_local(directory)

    vector_index = FAISS.load_local(settings.STATIC_ROOT, OpenAIEmbeddings())
    vector_index_entry = VectorIndex(context_id=context_id, index_directory=directory)
    vector_index_entry.save()
    retriever = vector_index.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    conv_interface = ConversationalRetrievalChain.from_llm(ChatOpenAI(temperature=0), retriever=retriever)

    chat_history = []
    result = conv_interface({"question": query, "chat_history": chat_history})
    chat_history.append((query, result["answer"]))
    # Save chat history to the database
    chat_entry = ChatHistory(user_id=user_id, context_id=context_id, question=query, answer=result["answer"],
                             conversation_history=chat_history,pdf_name=pdf_file_obj.name)
    chat_entry.save()
    return JsonResponse(
        {'status': 'success','message': "Uploaded successfully, you can now start a chat.", 'question': query,
         'answer': result['answer'], "context_id": context_id,"pdf_name": pdf_file_obj.name,
         'status_code': 200, },
        status=200)
    # except:
    #     return JsonResponse(
    #         {'status': 'error', 'message': "Something went wrong, please try again or contact support",
    #          'status_code': 400, },
    #         status=400)


@csrf_exempt
def continue_conversation(request):
    query = request.POST.get("query")
    user_id = request.POST.get("user_id")
    context_id = request.POST.get("context_id")
    print(f'{user_id} -- {context_id}')
    os.environ["OPENAI_API_KEY"] = settings.OPEN_AI_KEY

    chat_entries = ChatHistory.objects.get(user_id=user_id, context_id=context_id)
    print(chat_entries)
    chat_history = [(chat_entries.question, chat_entries.answer)]

    try:
        # Try to fetch vector index from the database using context_id
        vector_index = VectorIndex.objects.get(context_id=context_id)
    except VectorIndex.DoesNotExist:
        # Handle the case where vector index is not found
        return JsonResponse({"error": "Vector index not found for the given context ID"}, status=404)

    # Load the vector index for the retriever
    vector_index = FAISS.load_local(vector_index.index_directory, OpenAIEmbeddings())
    retriever = vector_index.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    asyncHandler = AsyncIteratorCallbackHandler()
    # Initialize ConversationalRetrievalChain without initial chat history
    conv_interface = ConversationalRetrievalChain.from_llm(ChatOpenAI(temperature=0, streaming=True),
                                                           callbacks=[asyncHandler], retriever=retriever, )

    async def test_stream():
        async for i in asyncHandler.aiter():
            print(i)

    test_stream()

    # Streaming generator function for response
    def stream_response():
        # Start the conversation with the chat_history input
        result = conv_interface({"question": query, "chat_history": chat_history})

        yield f"AI: {result['answer']}\n\n"

        # Update the chat history with the new conversation
        chat_history.append((query, result["answer"]))

    return StreamingHttpResponse(stream_response())


@csrf_exempt
def fetch_conversation_history(request):
    user_id = request.POST.get('user_id')
    chat_history = ChatHistory.objects.filter(user_id=user_id)
    chat_history_serializer = ChatHistorySerializer(chat_history,many=True).data
    return JsonResponse(
        {'status': 'success', 'message': "Fetched chat history successfully.", 'data': list(chat_history_serializer),
         'status_code': 200, },
        status=200)
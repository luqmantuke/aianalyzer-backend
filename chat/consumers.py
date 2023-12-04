import asyncio
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.conf import settings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import HumanMessagePromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from chat.models import ChatHistory, VectorIndex  # Replace with your actual model names
import os
from channels.db import database_sync_to_async


class OpenAIConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"type": 'connection','status': 'success', 'message': 'Connected Successfully',
                                              'status_code': 200}, ))
        query_string = self.scope['query_string'].decode('utf-8')
        parameters = parse_qs(query_string)

        user_id = parameters.get('user_id', [None])[0]
        context_id = parameters.get('context_id', [None])[0]
        chat_entries = await sync_to_async(ChatHistory.objects.get)(user_id=user_id, context_id=context_id)


        await self.send(
            text_data=json.dumps({"type": "chat_history", "chats": json.dumps(chat_entries.conversation_history)
                                  }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_id = data.get("user_id")
        context_id = data.get("context_id")
        query = data.get("query")
        os.environ["OPENAI_API_KEY"] = settings.OPEN_AI_KEY

        # Use sync_to_async for database operations
        chat_entries = await sync_to_async(ChatHistory.objects.get)(user_id=user_id, context_id=context_id)

        await self.send(text_data=json.dumps({"type": "loading","status": "loading", "message":"We're working on it..."
                                                 }))

        chat_history = [(item[0], item[1]) for item in chat_entries.conversation_history]

        try:
            vector_index = await sync_to_async(VectorIndex.objects.get)(context_id=context_id)

        except VectorIndex.DoesNotExist:

            pass

        vector_index = FAISS.load_local(vector_index.index_directory, OpenAIEmbeddings())
        retriever = vector_index.as_retriever(search_type="similarity", search_kwargs={"k": 6})
        system_template = """You have been provided with content extracted from a PDF and stored in context. 
        When answering questions, you should base your responses solely on the context 
        from this PDF. You can have normal conversation like greetings and answering common questions like 
        who are you and what you can help them with. Do not draw from any external knowledge or information outside 
        of what's in the content provided. Additionally,
         be attentive to correct any spelling mistakes in the queries you receive. Here's the context
                ----------------
                {context}"""

        # Create the chat prompt templates
        messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("{question}")
        ]
        qa_prompt = ChatPromptTemplate.from_messages(messages)

        async def create_conv_interface():
            conv = ConversationalRetrievalChain.from_llm(
                ChatOpenAI(),
                retriever=retriever,
                combine_docs_chain_kwargs={"prompt": qa_prompt},
                callbacks=[StreamingStdOutCallbackHandler()]

            )
            return conv

        conv_interface_sync = await create_conv_interface()
        # Start the conversation

        conv_state = conv_interface_sync({"question": query, "chat_history": chat_history})
        await self.send(text_data=json.dumps({ "type": "answer","question": query,"answer": conv_state["answer"],
         }))

        async def process_responses():
            chat_entries.conversation_history.append((query, conv_state["answer"]))

            await sync_to_async(chat_entries.save)()

        await process_responses()


from django.urls import re_path
from .consumers import OpenAIConsumer

websocket_urlpatterns = [
    re_path(r"ws/ai/", OpenAIConsumer.as_asgi()),
]

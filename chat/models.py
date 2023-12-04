from django.contrib.auth.models import User
from django.db import models
# import jsonfield
class VectorIndex(models.Model):
    context_id = models.CharField(primary_key=True, max_length=100)  # Identifier for the vector index (optional)
    index_directory = models.CharField(max_length=200)  # Directory path for index storage


class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User identifier or session ID
    context_id = models.CharField(max_length=100)  # Conversation or context identifier
    question = models.TextField()
    answer = models.TextField()
    conversation_history = models.JSONField(default=list)
    timestamp = models.DateTimeField(auto_now_add=True)
    pdf_name = models.CharField(max_length=1000)


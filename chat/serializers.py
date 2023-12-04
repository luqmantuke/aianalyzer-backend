from rest_framework import serializers
from .models import ChatHistory


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ('user','context_id','pdf_name','question','answer')


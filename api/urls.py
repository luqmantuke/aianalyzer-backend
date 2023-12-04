from django.urls import path
from chat.views import *
from analyzer.views import *
urlpatterns = [
    # chat
    path('upload_pdf_view/', upload_pdf_view),
    path('fetch_report/',fetch_report),
    path('ask_pdf/', ask_pdf),
    path('continue_conversation/', continue_conversation),
    path('fetch_conversation_history/', fetch_conversation_history),

    # authentication

    # path('rest/', include('rest_framework.urls')),

    #Authentication

]

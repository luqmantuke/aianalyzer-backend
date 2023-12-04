from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from aianalyzer import settings
from pdf2image import convert_from_path
import os
from django.http import JsonResponse
import boto3
import openai
import json
import re

from analyzer.models import Report
from analyzer.serializers import ReportSerializer


def analyze_images_with_openai_vision_api(image_urls):
    OPEN_AI_KEY = "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"
    client = openai.OpenAI(api_key=OPEN_AI_KEY)

    system_prompt = {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": """You are a highly advanced AI capable of analyzing images.
                      Your responses should include detailed descriptions of the content and context of each image.
                        Extract and present information in a structured JSON format, highlighting key elements such 
                        as objects, people, activities, settings, and any text present. Compare and contrast images 
                        when multiple are provided. Respond to user queries by focusing on the visual details and 
                        their potential significance.You can skip a slide(image) if it's blank or you don't understand.
                        Please return result as json data like this. {'title': {},'summary': {},
                         'data': [ "slide_title": '',
                "content": '',
                "image_url": ''].
 }. Please return content Json format  with no any other words or explanations.Strictly json format. For example ```json
```json you returned should be removed and just return json format content.
                 """
            },


        ],

    }

    user_message = {
        "role": "user",
        "content": [
                       {
                           "type": "text",
                           "text": "Please look through these images and then summarize them,"
                                   " generating a report with each image URL included. Include the image url that you used to intepret",
                       }
                   ] + [{"type": "image_url", "image_url": {"url": url}} for url in image_urls]
    }

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[system_prompt, user_message],
        max_tokens=4000
    )
    if response.choices:
        response_text = response.choices[0]
        first_choice = response_text
        # Accessing the 'message' attribute of the first 'Choice' object
        chat_message = first_choice.message

        # Finally, accessing the 'content' key in 'ChatCompletionMessage'
        content = chat_message.content

        # Now, 'content' variable holds the data you're interested in
        report = Report.objects.create(data=content,image_urls=image_urls)

        return  {'status': 'success', 'message': "Analyzed Successfully you can now view the report", 'report_id': report.id,
             'status_code': 200, }



def upload_files(file_names, bucket_name):
    """
    Upload multiple files to an S3 bucket and return their download URLs.
    
    :param file_names: List of file paths to upload
    :param bucket_name: Name of the S3 bucket
    :return: List of download URLs
    """
    # Creating an S3 client
    s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                      region_name=settings.AWS_S3_REGION_NAME)

    urls = []

    for file_name in file_names:
        try:
            # Upload file
            s3.upload_file(file_name, bucket_name, file_name)

            # Generate download URL
            url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
            urls.append(url)

        except:
            print(f"The file {file_name} was not found.")

    return urls


def extract_pdf_file(input_path):
    # Convert PDF to images
    pages = convert_from_path(input_path, 200)
    image_paths = []
    for count, page in enumerate(pages):
        image_path = f'tmp_environmental{count}.jpg'
        page.save(image_path, 'JPEG')
        image_paths.append(image_path)

    return image_paths


def upload_and_cleanup(image_paths, bucket_name):
    # Upload files to S3 and get URLs
    download_urls = upload_files(image_paths, bucket_name)

    # Delete temporary files
    for path in image_paths:
        os.remove(path)

    return download_urls


@csrf_exempt
def upload_pdf_view(request):
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        if pdf_file:
            # Save the file temporarily
            temp_pdf_path = os.path.join(settings.STATIC_ROOT, 'temp_uploaded_file.pdf')
            with open(temp_pdf_path, 'wb+') as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)

            # Extract images from PDF
            image_paths = extract_pdf_file(temp_pdf_path)

            # Upload to S3 and clean up
            my_bucket = settings.AWS_STORAGE_BUCKET_NAME
            download_urls = upload_and_cleanup(image_paths, my_bucket)

            # Delete the temporary PDF file
            os.remove(temp_pdf_path)
            analysis_report = analyze_images_with_openai_vision_api(download_urls)

            # Return the analysis report with URLs in JSON format
            return JsonResponse(analysis_report)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def fetch_report(request):
    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        print(report_id)
        report = Report.objects.get(id=report_id)
        report_serializer = ReportSerializer(report).data
        return JsonResponse({'status':'success','message':'report fetched successfully','data':report_serializer})

    return JsonResponse({'error': 'Invalid request'}, status=400)

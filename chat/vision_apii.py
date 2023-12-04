from openai import OpenAI


OPEN_AI_KEY = "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"

client = OpenAI(api_key=OPEN_AI_KEY)

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
               their potential significance.You can skip a slide(image) if it's blank or you don't understand."""
        }
    ]
}
image_urls = [
    "https://ommyfitnessbucket.s3.amazonaws.com/environmental1.jpg",
    "https://ommyfitnessbucket.s3.amazonaws.com/environmental2.jpg",
    "https://ommyfitnessbucket.s3.amazonaws.com/environmental3.jpg",
    "https://ommyfitnessbucket.s3.amazonaws.com/environmental4.jpg",
    "https://ommyfitnessbucket.s3.amazonaws.com/environmental5.jpg",
    "https://ommyfitnessbucket.s3.amazonaws.com/environmental6.jpg",
    "https://ommyfitnessbucket.s3.amazonaws.com/environmental7.jpg",
    "https://ommyfitnessbucket.s3.amazonaws.com/environmental8.jpg",
    "https://ommyfitnessbucket.s3.amazonaws.com/environmental9.jpg",

]

# Constructing the user message with the list of image URLs
user_message = {
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "Please look through these images and then summarize them, generating a report with each image URL included.",
        }
    ] + [{"type": "image_url", "image_url": {"url": url}} for url in image_urls]
}

response = client.chat.completions.create(
  model="gpt-4-vision-preview",
  messages=[
  system_prompt,
  user_message
  ],
max_tokens=4000
)

print(response.choices[0])

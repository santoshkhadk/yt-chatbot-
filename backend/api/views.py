from rest_framework.decorators import api_view
from rest_framework.response import Response
from rag.rag_pipeline import answer_youtube_question 


import os
from dotenv import load_dotenv

# load .env file
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

@api_view(['POST'])
def ask_question(request):
    video_url = request.data.get("url")
    question = request.data.get("question")

    # Extract YouTube video ID
    video_id = video_url.split("v=")[-1]

    answer = answer_youtube_question(video_id, question, API_KEY)

    return Response({"answer": answer})
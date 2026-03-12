# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rag.rag_pipeline import answer_question_multi_video
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")


@api_view(['POST'])
def ask_question(request):
    """
    Accepts JSON:
    {
        "urls": ["https://www.youtube.com/watch?v=VIDEO_ID1", "https://www.youtube.com/watch?v=VIDEO_ID2"],
        "question": "Your question here"
    }
    """
    video_urls = request.data.get("urls", [])
    question = request.data.get("question")

    if not video_urls or not question:
        return Response({"error": "Video URLs and question are required"}, status=400)

    answer = answer_question_multi_video(video_urls, question, API_KEY)
    return Response({"answer": answer})
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
    Request payload:
    {
        "urls": ["https://youtube.com/watch?v=abc", "https://youtube.com/watch?v=def"],
        "question": "Explain Python loops"
    }
    Optional file: transcript_file
    """

    # get list of video URLs
    video_urls = request.data.get("urls")

    # question string
    question = request.data.get("question")

    # transcript file if uploaded
    transcript_file = request.FILES.get("transcript_file")

    # run RAG pipeline
    result = answer_question_multi_video(
        video_urls,
        transcript_file,
        question,
        API_KEY
    )

    return Response(result)
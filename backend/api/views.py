from rest_framework.decorators import api_view
from rest_framework.response import Response
from rag.rag_pipeline import answer_question_multi_video
import os
from dotenv import load_dotenv

load_dotenv()

print(os.getenv("GROQ_API_KEY"))
API_KEY = os.getenv("GROQ_API_KEY")
print(API_KEY)


@api_view(['POST'])
def ask_question(request):

    video_urls = request.data.getlist("urls")
    question = request.data.get("question")
    print(API_KEY)
    transcript_file = request.FILES.get("transcript_file")

    answer = answer_question_multi_video(
        video_urls,
        transcript_file,
        question,
        API_KEY
    )

    return Response({"answer": answer})
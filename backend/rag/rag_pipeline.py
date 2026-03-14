from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

import pdfplumber


# --------------------------------------
# Extract YouTube Video ID
# --------------------------------------

def extract_video_id(url: str) -> str | None:
    query = parse_qs(urlparse(url).query)
    return query.get("v", [None])[0]


# --------------------------------------
# Fetch Transcript Safely
# --------------------------------------

def fetch_transcript_safe(video_id: str) -> str | None:

    for lang in ["en", "en-auto"]:
        try:
            transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=[lang])
            return " ".join([t.text for t in transcript_list])
        except (TranscriptsDisabled, NoTranscriptFound):
            continue
        except Exception:
            continue

    return None


# --------------------------------------
# Get transcripts from multiple videos
# --------------------------------------

def get_multi_video_transcript(video_urls: list[str]) -> str:

    transcripts = []

    for i, url in enumerate(video_urls):

        video_id = extract_video_id(url)

        if not video_id:
            transcripts.append(f"[Video {i+1}] Invalid URL")
            continue

        text = fetch_transcript_safe(video_id)

        if text:
            transcripts.append(f"[Video {i+1}]\n{text}")
        else:
            transcripts.append(f"[Video {i+1}] Transcript not available")

    return "\n\n".join(transcripts)


# --------------------------------------
# Read uploaded transcript file
# --------------------------------------

def read_uploaded_transcript(file):

    if not file:
        return ""

    try:

        # TXT file
        if file.name.endswith(".txt"):
            return file.read().decode("utf-8")

        # PDF file
        if file.name.endswith(".pdf"):

            text = ""

            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()

                    if page_text:
                        text += page_text + "\n"

            return text

    except Exception:
        return ""

    return ""


# --------------------------------------
# MAIN RAG PIPELINE
# --------------------------------------

def answer_question_multi_video(video_urls: list[str], transcript_file, question: str, api_key: str):

    # 1️⃣ Get video transcripts
    video_text = get_multi_video_transcript(video_urls)

    # 2️⃣ Get uploaded transcript
    uploaded_text = read_uploaded_transcript(transcript_file)

    # 3️⃣ Combine both sources
    combined_text = video_text + "\n" + uploaded_text

    if not combined_text.strip():
        return "No transcript available from videos or uploaded file."

    # --------------------------------------

    # Split text
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_text(combined_text)

    # --------------------------------------

    # Embeddings + FAISS
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = FAISS.from_texts(chunks, embedding_model)

    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # --------------------------------------

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Prompt
    prompt_template = """
Use the context below to answer the question.

Context:
{context}

Question:
{question}

Answer:
"""

    PROMPT = PromptTemplate(
        input_variables=["context", "question"],
        template=prompt_template
    )

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=api_key
    )

    # --------------------------------------

    parallel_chain = RunnableParallel({
        "context": retriever | RunnableLambda(format_docs),
        "question": RunnablePassthrough()
    })

    rag_chain = parallel_chain | PROMPT | llm | StrOutputParser()

    answer = rag_chain.invoke(question)

    return answer
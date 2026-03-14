from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_core.documents import Document


import pdfplumber


# --------------------------------------
# Extract YouTube Video ID
# --------------------------------------

def extract_video_id(url: str) -> str | None:
    query = parse_qs(urlparse(url).query)
    return query.get("v", [None])[0]


# --------------------------------------
# Fetch Transcript with timestamps
# --------------------------------------

def fetch_transcript_safe(video_id: str):

    for lang in ["en", "en-auto"]:
        try:
            transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=[lang])
            return transcript_list
        except (TranscriptsDisabled, NoTranscriptFound):
            continue
        except Exception:
            continue

    return None


# --------------------------------------
# Convert transcripts to documents
# --------------------------------------

def get_multi_video_documents(video_urls):

    docs = []

    for url in video_urls:

        video_id = extract_video_id(url)

        if not video_id:
            continue

        transcript = fetch_transcript_safe(video_id)

        if not transcript:
            continue

        for t in transcript:

            docs.append(
                Document(
                    page_content=t.text,
                    metadata={
                        "video_url": url,
                        "timestamp": int(t.start)
                    }
                )
            )

    return docs


# --------------------------------------
# Read uploaded transcript file
# --------------------------------------

def read_uploaded_transcript(file):

    if not file:
        return []

    try:

        # TXT
        if file.name.endswith(".txt"):

            text = file.read().decode("utf-8")

            return [Document(page_content=text, metadata={"source": "uploaded"})]

        # PDF
        if file.name.endswith(".pdf"):

            text = ""

            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            return [Document(page_content=text, metadata={"source": "uploaded"})]

    except Exception:
        return []

    return []


# --------------------------------------
# MAIN RAG PIPELINE
# --------------------------------------

def answer_question_multi_video(video_urls, transcript_file, question, api_key):

    # 1️⃣ Get documents from videos
    video_docs = get_multi_video_documents(video_urls)

    # 2️⃣ Get uploaded transcript docs
    uploaded_docs = read_uploaded_transcript(transcript_file)

    docs = video_docs + uploaded_docs

    if not docs:
        return {"answer": "No transcript available.", "sources": []}

    # --------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    split_docs = splitter.split_documents(docs)

    # --------------------------------------

    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = FAISS.from_documents(split_docs, embedding_model)

    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # --------------------------------------

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

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
        "context": retriever,
        "question": RunnablePassthrough()
    })

    rag_chain = parallel_chain | RunnableLambda(
        lambda x: {
            "context": format_docs(x["context"]),
            "question": x["question"],
            "docs": x["context"]
        }
    ) | RunnableLambda(
        lambda x: {
            "answer": (PROMPT | llm | StrOutputParser()).invoke({
                "context": x["context"],
                "question": x["question"]
            }),
            "sources": x["docs"]
        }
    )

    result = rag_chain.invoke(question)

    # --------------------------------------
    # Extract timestamp links
    # --------------------------------------

    sources = []

    for d in result["sources"]:

        if "video_url" in d.metadata:

            timestamp = d.metadata["timestamp"]
            url = d.metadata["video_url"]

            sources.append({
                "text": d.page_content,
                "timestamp": timestamp,
                "link": f"{url}&t={timestamp}s"
            })
    

    return {
        "answer": result["answer"].replace("\n", " ").strip(),
        "sources": sources
    }
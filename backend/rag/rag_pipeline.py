from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

def extract_video_id(url: str) -> str | None:
    """Extract the video ID from a YouTube URL"""
    query = parse_qs(urlparse(url).query)
    return query.get("v", [None])[0]

def fetch_transcript_safe(video_id: str) -> str | None:
    """Try to fetch English or auto-generated transcript"""
    for lang in ['en', 'en-auto']:
        try:
            transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=[lang])
            print(transcript_list)
            return " ".join([t.text for t in transcript_list])  # <-- updated
        except (TranscriptsDisabled, NoTranscriptFound):
            continue
        except Exception:
            continue
    return None

def get_multi_video_transcript(video_urls: list[str]) -> str:
    """Fetch and aggregate transcripts from multiple YouTube URLs"""
    all_transcripts = []

    for i, url in enumerate(video_urls):
        video_id = extract_video_id(url)
        if not video_id:
            all_transcripts.append(f"[Video {i+1}] [Invalid URL]")
            continue

        transcript_text = fetch_transcript_safe(video_id)
        if transcript_text:
            all_transcripts.append(f"[Video {i+1}]\n{transcript_text}")
        else:
            all_transcripts.append(f"[Video {i+1}] [Transcript not available]")

    return "\n\n".join(all_transcripts)

def answer_question_multi_video(video_urls: list[str], question: str, api_key: str) -> str:
    """RAG pipeline for multiple YouTube videos"""
    aggregated_transcript = get_multi_video_transcript(video_urls)
    
    # Split text
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(aggregated_transcript)

    # Embeddings + FAISS
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = FAISS.from_texts(chunks, embedding_model)
    retriever = vector_store.as_retriever(search_kwargs={"k":3})

    # Format docs
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # LLM + Prompt
    prompt_template = """
Use the context to answer the question.

Context:
{context}

Question:
{question}

Answer:
"""
    PROMPT = PromptTemplate(input_variables=["context","question"], template=prompt_template)
    llm = ChatGroq(model="llama-3.1-8b-instant", api_key=api_key)

    parallel_chain = RunnableParallel({
        "context": retriever | RunnableLambda(format_docs),
        "question": RunnablePassthrough()
    })

    rag_chain = parallel_chain | PROMPT | llm | StrOutputParser()
    answer = rag_chain.invoke(question)
    return answer
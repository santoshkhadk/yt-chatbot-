from youtube_transcript_api import YouTubeTranscriptApi
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

def answer_youtube_question(video_id, question, api_key):
    # 1️⃣ Fetch transcript
    transcript = YouTubeTranscriptApi().fetch(video_id, languages=['en'])
    text = " ".join([t['text'] for t in transcript.to_raw_data()])

    # 2️⃣ Split text
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)

    # 3️⃣ Embeddings + Vector Store (in memory)
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = FAISS.from_texts(chunks, embedding_model)

    # 4️⃣ Retriever
    retriever = vector_store.as_retriever(search_kwargs={"k":3})

    # 5️⃣ Format docs
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # 6️⃣ LLM + Prompt
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

    # 7️⃣ Return answer
    answer = rag_chain.invoke(question)
    return answer
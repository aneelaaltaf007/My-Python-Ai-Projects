# import libraries
import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
import re


st.set_page_config(
    page_title="Document Q&A",
    page_icon="📚",
    layout="wide"
)


def extract_text(uploaded_file):
    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "pdf":
        reader = PdfReader(uploaded_file)
        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        return text

    elif file_type == "docx":
        document = Document(uploaded_file)
        text = ""

        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"

        return text

    elif file_type == "txt":
        return uploaded_file.read().decode("utf-8", errors="ignore")

    return ""


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def create_chunks(text, chunk_size=350):
    text = clean_text(text)

    if not text:
        return []

    words = text.split()
    chunks = []

    for start in range(0, len(words), chunk_size):
        chunks.append(
            " ".join(words[start:start + chunk_size])
        )

    return chunks


def find_relevant_chunks(question, chunks, max_chunks=2):
    question_words = set(
        re.findall(r"\b[a-zA-Z0-9]+\b", question.lower())
    )

    scored_chunks = []

    for chunk in chunks:
        chunk_words = set(
            re.findall(r"\b[a-zA-Z0-9]+\b", chunk.lower())
        )

        score = len(question_words.intersection(chunk_words))

        scored_chunks.append((score, chunk))

    scored_chunks.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        chunk
        for score, chunk in scored_chunks[:max_chunks]
    ]


def generate_response(uploaded_file, user_query, api_key):

    document_text = extract_text(uploaded_file)

    if not document_text.strip():
        return "Could not extract any text from the uploaded document."

    chunks = create_chunks(document_text)

    relevant_chunks = find_relevant_chunks(
        user_query,
        chunks,
        max_chunks=2
    )

    context = "\n\n".join(relevant_chunks)

    client = Groq(api_key=api_key)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful Document AI Assistant. "
                "Answer only using the provided document context. "
                "Do not invent information. "
                "If the answer is not found in the document, "
                "say that the information was not found."
            )
        },
        {
            "role": "user",
            "content": f"""
Document context:

{context}

Question:

{user_query}
"""
        }
    ]

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        temperature=0.2,
        max_completion_tokens=600
    )

    return response.choices[0].message.content


st.title("📚 Document Question Answering")

st.write(
    "Upload a TXT, PDF, or Word document and ask questions about it."
)


# Sidebar API Key
with st.sidebar:
    st.header("⚙️ Settings")

    api_key = st.text_input(
        "🔑 Groq API Key",
        type="password",
        placeholder="Enter your Groq API key"
    )


uploaded_file = st.file_uploader(
    "📂 Upload your document",
    type=["txt", "pdf", "docx"]
)


if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")


user_query = st.text_input(
    "❓ Ask a question about your document",
    placeholder="Example: What is this document about?"
)


if st.button("🚀 Get Answer"):

    if not api_key:
        st.warning("Please enter your Groq API key in the sidebar.")

    elif not uploaded_file:
        st.warning("Please upload a document.")

    elif not user_query:
        st.warning("Please enter your question.")

    else:

        with st.spinner("Reading document and generating answer..."):

            try:
                answer = generate_response(
                    uploaded_file,
                    user_query,
                    api_key
                )

                st.subheader("💡 Answer")
                st.write(answer)

            except Exception as e:
                st.error(f"Error: {e}")
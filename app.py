import hashlib
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from rag import answer_question, index_pdf

load_dotenv()

MAX_PDF_SIZE = 20 * 1024 * 1024
UPLOAD_DIR = Path(os.getenv("RAG_DATA_DIR", "./data")) / "uploads"

st.set_page_config(page_title="PDF Question Answering", page_icon="📄")
st.title("PDF Question Answering")
st.write("Upload one or more PDFs, index them, then ask questions about their contents.")

if not os.getenv("GROQ_API_KEY"):
    st.warning("Set GROQ_API_KEY in your environment or local .env file to ask questions.")

uploaded_files = st.file_uploader(
    "Choose PDF files",
    type=["pdf"],
    accept_multiple_files=True,
    help="Each PDF must be 20 MB or smaller.",
)

if st.button("Index PDFs", disabled=not uploaded_files):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.size > MAX_PDF_SIZE:
                st.error(f"{uploaded_file.name} exceeds the 20 MB upload limit.")
                continue
            if not uploaded_file.getvalue():
                st.error(f"{uploaded_file.name} is empty.")
                continue

            content = uploaded_file.getvalue()
            content_hash = hashlib.sha256(content).hexdigest()
            saved_path = UPLOAD_DIR / f"{content_hash}.pdf"
            if not saved_path.exists():
                saved_path.write_bytes(content)

            with st.spinner(f"Processing {uploaded_file.name}..."):
                chunk_count = index_pdf(saved_path, source_name=uploaded_file.name)
            if chunk_count:
                st.success(f"Indexed {chunk_count} chunks from {uploaded_file.name}.")
            else:
                st.info(f"{uploaded_file.name} is already indexed.")
        except Exception as exc:
            st.error(f"Could not process {uploaded_file.name}: {exc}")

with st.form("question_form"):
    question = st.text_input("Your question")
    submitted = st.form_submit_button("Ask")

if submitted:
    if not question.strip():
        st.error("Enter a question before submitting.")
    else:
        try:
            with st.spinner("Searching your PDFs and generating an answer..."):
                answer = answer_question(question)
            st.subheader("Answer")
            st.write(answer)
        except Exception as exc:
            st.error(f"Could not answer the question: {exc}")

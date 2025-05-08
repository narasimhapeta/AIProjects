import streamlit as st
import faiss
import numpy as np
import PyPDF2
import textwrap
import os
from openai import OpenAI

# Load API key from environment variable - Provide your OpenAI API Key here
client = OpenAI(api_key="")

# === PDF Extraction ===
def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# === Chunking ===
def chunk_text(text, max_tokens=500):
    return textwrap.wrap(text, max_tokens)

# === Embedding ===
def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[text]
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

# === FAISS Index Building ===
def build_faiss_index(chunks):
    embeddings = [get_embedding(chunk) for chunk in chunks]
    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))
    return index, embeddings

# === Similarity Search ===
def search_index(index, chunks, query, k=3):
    query_embedding = get_embedding(query).reshape(1, -1)
    distances, indices = index.search(query_embedding, k)
    return [chunks[i] for i in indices[0]]

# === Generate Answer ===
def generate_answer(context_chunks, question):
    context = "\n".join(context_chunks)
    prompt = f"""You are an assistant that answers based only on internal company policy.

Context:
{context}

Question: {question}

Answer:"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

# === Streamlit UI ===
st.title("📄 Company Policy AI Assistant")

uploaded_file = st.file_uploader("Upload a policy PDF", type=["pdf"])

if uploaded_file:
    st.success("PDF uploaded successfully!")
    raw_text = extract_text_from_pdf(uploaded_file)
    chunks = chunk_text(raw_text)
    st.write(f"Document split into {len(chunks)} chunks.")
    
    st.session_state['chunks'] = chunks
    index, _ = build_faiss_index(chunks)
    st.session_state['index'] = index

    st.write("---")
    question = st.text_input("Ask a question based on the policy:")
    
    if question and st.session_state.get('index'):
        with st.spinner("Thinking..."):
            top_chunks = search_index(st.session_state['index'], st.session_state['chunks'], question)
            answer = generate_answer(top_chunks, question)
            st.markdown("**Answer:**")
            st.write(answer)

# 📄 RAG Study Assistant (Hosted + Local Hybrid)

A **document-based AI assistant** that lets you upload files and chat with them using **Retrieval-Augmented Generation (RAG)**.

This project is built as a **production-style system** with:

* modular architecture
* pluggable LLM backends
* persistent chat sessions
* deployable infrastructure (no local model dependency required)

---

## 🎯 What This Solves

Traditional LLMs often hallucinate or provide generic answers.

This app:

* retrieves **relevant chunks from your document**
* uses them as **context for the LLM**
* ensures answers are **grounded, explainable, and reliable**

---

## 🧠 Core Concept: RAG

Retrieval-Augmented Generation works as follows:

1. Upload document
2. Split into chunks
3. Convert chunks → embeddings
4. Store in FAISS vector database
5. On query:

   * retrieve relevant chunks
   * pass them to LLM
   * generate contextual answer

---

## ✨ Features

* 📁 Upload documents (`PDF`, `DOCX`, `PPTX`, `TXT`)
* 💬 Chat-style interface (ChatGPT-like UX)
* 🧠 True Retrieval-Augmented Generation
* 🔍 Semantic search using FAISS
* 💾 Persistent chat history per document
* ⚡ Hosted LLM support (Groq)
* 🪂 Fallback LLM support (OpenRouter)
* 🧩 Modular embedding + LLM backend
* 🌐 Fully deployable (no Ollama required)

---

## 🏗️ Architecture

```
User
│
▼
Streamlit UI
│
├── Upload Page
├── Chat Page
├── Chat History
│
▼
FAISS Vector Store (per document)
│
▼
Embedding Model (HuggingFace MiniLM)
│
▼
LLM Layer
   ├── Primary: Groq (LLaMA 3)
   └── Fallback: OpenRouter (Nemotron)
```

---

## ⚙️ Tech Stack

* **Frontend:** Streamlit
* **Backend:** Python
* **LLM:** Groq (primary), OpenRouter (fallback)
* **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)
* **Vector DB:** FAISS
* **Document Parsing:** PyPDF, Unstructured, Docx2txt

---

## 🚀 Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/rag-study-assistant.git
cd rag-study-assistant
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv .venv
```

Activate it:

**Windows**

```bash
.venv\Scripts\activate
```

**Mac/Linux**

```bash
source .venv/bin/activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Configure Environment Variables

Create a `.env` file in the root directory:

```env
LLM_BACKEND=hosted

# Groq (Primary LLM)
GROQ_API_KEY=your_groq_api_key

# OpenRouter (Fallback LLM)
OPENROUTER_API_KEY=your_openrouter_api_key
```

---

### 5️⃣ Run the Application

```bash
streamlit run ui.py
```

Open in browser:

```
http://localhost:8501
```

---

## 🧪 How It Works (Execution Flow)

1. User uploads a document
2. Document is parsed and cleaned
3. Text is split into chunks
4. Chunks are embedded using MiniLM
5. Stored in FAISS vector database
6. User asks a question
7. Relevant chunks are retrieved
8. Context is sent to LLM
9. LLM generates grounded response

---

## 🧠 LLM Strategy

| Layer      | Model                      | Purpose            |
| ---------- | -------------------------- | ------------------ |
| Primary    | Groq LLaMA 3.1 8B          | Fast responses ⚡   |
| Fallback   | Nemotron (OpenRouter free) | Reliability 🪂     |
| Embeddings | MiniLM                     | Lightweight + fast |

---

## ⚡ Key Design Decisions

* **One document = one FAISS index**
* **Vector DB treated as cache**
* **Chat history stored separately**
* **Modular LLM + embedding backend**
* **Failover system for reliability**

---

## 🗂️ Project Structure

```
rag-project/
│
├── loaders/              # Document loaders
├── chunking/             # Text splitting logic
├── embeddings/           # Embedding model
├── vector_store/         # FAISS management
├── llm/                  # LLM configuration
│
├── pages/
│   ├── 1_Chats.py
│   └── 2_Chat.py
│
├── ui.py                 # Main entry point
├── chat_store.json       # Chat persistence
├── requirements.txt
└── README.md
```

---

## ⚠️ Known Limitations

* Some PDFs may fail due to malformed structure (PyPDF limitation)
* Lightweight embeddings → slightly lower semantic accuracy
* Free-tier APIs may have rate limits

---

## 🚀 Future Improvements

* 🔁 Hybrid search (BM25 + vector)
* 🎯 Reranking models
* 🧠 Query rewriting
* 📊 Source highlighting
* 🌐 Multi-user support
* 📁 File preview panel

---

## 👤 Author

**Anirudh Kambampati**

---

## 📜 License

MIT License. See the [LICENSE](LICENSE) file for more information.

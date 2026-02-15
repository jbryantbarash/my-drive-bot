# 🤖 Google Drive AI Assistant (RAG)

A sophisticated **Retrieval-Augmented Generation (RAG)** chatbot that connects to Google Drive to answer questions about your personal documents. 

This assistant doesn't just search for files; it "reads" them using **Claude 3** and specialized parsers to provide summarized insights from PDFs, Word docs, and Google Docs.



## 🚀 Features
* **Deep Document Parsing:** Integrated with `PyPDF2` and `docx2txt` to extract text from binary files.
* **Intelligent Agentic Search:** Uses **LangGraph** to autonomously decide when to query Google Drive based on user intent.
* **Secure Authentication:** Implements Google OAuth2 for secure, user-authorized access to Drive metadata and content.
* **Streamlit Interface:** A clean, responsive chat UI for real-time interaction.

## 🛠️ Tech Stack
* **LLM:** Claude 3 (Anthropic)
* **Orchestration:** LangChain & LangGraph
* **APIs:** Google Drive API v3
* **Frontend:** Streamlit
* **Environment:** Python 3.11+

## 📦 Installation & Setup

1. **Clone the Repo:**
   ```bash
   git clone https://github.com/jbryantbarash/my-drive-bot.git
   cd my-drive-bot
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys:**
   * Place your Google `credentials.json` in the root folder.
   * Create a `.env` file and add: `ANTHROPIC_API_KEY=your_key_here`

4. **Run the App:**
   ```bash
   python -m streamlit run app.py
   ```

---
*Developed as a personal tool to bridge the gap between cloud storage and generative AI.*

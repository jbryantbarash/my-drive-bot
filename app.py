import streamlit as st
import os.path
import io
import docx2txt
from PyPDF2 import PdfReader
from dotenv import load_dotenv

# Google API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# LangChain / Anthropic
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# 1. Setup & Auth
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

# 2. Optimized Search Tool (Handles Docs, PDFs, and Word)
@tool
def search_drive(query: str):
    """
    Searches Jason's Google Drive and reads the content of relevant files.
    Use this for questions about Jason's identity, resume, or work history.
    """
    try:
        service = get_drive_service()
        # Search metadata for the query
        search_string = f"name contains '{query}' or fullText contains '{query}'"
        results = service.files().list(q=search_string, pageSize=3, fields="files(id, name, mimeType)").execute()
        items = results.get('files', [])

        if not items:
            return f"No documents found matching '{query}'."

        output = ""
        for item in items:
            f_id, f_name, f_type = item['id'], item['name'], item['mimeType']
            output += f"\n--- READING FILE: {f_name} ---\n"
            
            try:
                # TYPE 1: Google Doc
                if f_type == 'application/vnd.google-apps.document':
                    content = service.files().export(fileId=f_id, mimeType='text/plain').execute()
                    output += content.decode('utf-8')[:2000]
                
                # TYPE 2: PDF
                elif f_type == 'application/pdf':
                    request = service.files().get_media(fileId=f_id)
                    file_stream = io.BytesIO(request.execute())
                    reader = PdfReader(file_stream)
                    pdf_text = "".join([page.extract_text() for page in reader.pages[:2]])
                    output += pdf_text[:2000]

                # TYPE 3: Word Doc (.docx)
                elif f_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    request = service.files().get_media(fileId=f_id)
                    file_stream = io.BytesIO(request.execute())
                    output += docx2txt.process(file_stream)[:2000]
                
                else:
                    output += f"(Found file {f_name}, but it is a format I cannot read yet.)"
            except Exception as e:
                output += f"(Error reading file {f_name}: {str(e)})"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"

# 3. UI Setup
st.set_page_config(page_title="Jason's Drive Assistant", page_icon="🤖")
st.title("🤖 Jason's Drive Assistant")

# Initialize Agent
if "agent" not in st.session_state:
    llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)
    system_msg = (
        "You are Jason's personal assistant. You have access to his Google Drive. "
        "When asked about Jason's details, you MUST use the search_drive tool. "
        "If the search returns content from a PDF or Doc, analyze it carefully to provide a summary."
    )
    st.session_state.agent = create_react_agent(llm, [search_drive], prompt=system_msg)

# 4. Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Execution
if prompt := st.chat_input("Ask about your Drive..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        with st.status("🔍 Accessing Drive files...", expanded=False) as status:
            full_response = ""
            for chunk in st.session_state.agent.stream({"messages": [HumanMessage(content=prompt)]}):
                if "agent" in chunk:
                    full_response = chunk["agent"]["messages"][-1].content
                    response_placeholder.markdown(full_response)
                elif "tools" in chunk:
                    st.write(f"Reading content for context...")
            status.update(label="Analysis complete!", state="complete")
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

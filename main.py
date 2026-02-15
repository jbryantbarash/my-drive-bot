import os.path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

load_dotenv()

# The permission we need
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

@tool
def search_drive(query: str):
    """Searches Jason's Google Drive for his last name, resume, or bio."""
    try:
        service = get_drive_service()
        # 1. Search for files with 'Jason' or 'Resume' in the name
        search_query = "name contains 'Jason' or name contains 'Resume'"
        results = service.files().list(q=search_query, pageSize=5, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            return "No relevant files found."

        output = ""
        for item in items:
            file_id = item['id']
            # 2. Get the content of the file
            # Note: This works best for Google Docs. 
            # For PDFs, it will return metadata, but for a last name, the title often helps!
            output += f"\nFound File: {item['name']}\n"
            
            # If it's a Google Doc, export it as text
            try:
                content = service.files().export(fileId=file_id, mimeType='text/plain').execute()
                output += content.decode('utf-8')[:1000]
            except:
                output += "(Could not read full text, but file exists.)"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"

# Setup Agent
llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)
system_msg = "You are Jason's assistant. Use search_drive to find his last name. If you see a file like 'Jason_Barash_Resume', his last name is Barash."
agent = create_react_agent(llm, [search_drive], prompt=system_msg)

def run_chat():
    print("\n🚀 DriveBot is online! (Standard API Mode)")
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit"]: break
        for chunk in agent.stream({"messages": [("user", user_input)]}):
            if "agent" in chunk:
                print(f"AI: {chunk['agent']['messages'][-1].content}")

if __name__ == "__main__":
    run_chat()


# 3. System Instructions
system_message = (
    "You are Jason's personal AI assistant. You have access to his Google Drive. "
    "When asked about Jason's identity, last name, or work, you MUST call 'search_drive'. "
    "Read the provided document text carefully to find the answer."
)

# 4. Initialize LLM & Agent
llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)
tools = [search_drive]

# Using 'prompt' instead of 'state_modifier' 
# This is the most common fix for this specific TypeError
agent = create_react_agent(
    llm, 
    tools, 
    prompt=system_message
)

# 5. The Debug-Enabled Chat Loop
def run_chat():
    print("\n🚀 DriveBot is online! (Type 'exit' to quit)")
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        # Stream the agent's thought process
        for chunk in agent.stream({"messages": [("user", user_input)]}):
            # This prints the raw logic so we can see the tool output
            if "tools" in chunk:
                print(f"\n[TOOL OUTPUT]: {chunk['tools']['messages'][0].content[:200]}...") 
            
            if "agent" in chunk:
                answer = chunk["agent"]["messages"][-1].content
                if answer:
                    print(f"\nAI: {answer}")

if __name__ == "__main__":
    run_chat()

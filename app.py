from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
import os
import shelve
from lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete, gpt_4o_complete
import textract
from unstructured.partition.auto import partition
import glob
import time

load_dotenv()

st.title("Duke ProfMatch")



USER_AVATAR = "👤"
BOT_AVATAR = "🤖"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set up LightRAG
WORKING_DIR = "./data/Affiliations/"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

## Compressing the content
import pandas as pd
df = pd.read_csv(WORKING_DIR + 'Affiliations_sheet.csv')
df[:100].to_csv(WORKING_DIR + 'Affiliations_sheet_compressed.csv', index=False)
file_path = WORKING_DIR + 'Affiliations_sheet_compressed.csv'
text_content = textract.process(file_path)
####################

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=gpt_4o_mini_complete,  # Use gpt_4o_mini_complete LLM model
     llm_model_max_async=1
    # llm_model_func=gpt_4o_complete  # Optionally, use a stronger model
)


# Ensure openai_model is initialized in session state
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"

# Load chat history from shelve file
def load_chat_history():
    with shelve.open("chat_history") as db:
        return db.get("messages", [])


# Save chat history to shelve file
def save_chat_history(messages):
    with shelve.open("chat_history") as db:
        db["messages"] = messages

# Initialize or load chat history
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()
    
st.logo("./static/duke_match2.png", size = "large")

uploaded_file = st.file_uploader('Upload your resume/cv here:', type="pdf")
if uploaded_file is not None:
    file_elements = partition(file = uploaded_file)
    processed_file = "This should be a special case for the embedding. Make a special graph attribute as 'Me': \n" + "\n".join([str(i) for i in file_elements])
    rag.insert(processed_file)


# Sidebar with a button to delete chat history
with st.sidebar:
    if st.button("Delete Chat History"):
        st.session_state.messages = []
        save_chat_history([])
    if st.button("Reload LightRAG"):
        # Find all JSON and GraphML files in the specified folder
        file_patterns = ['*.json', '*.graphml']
        files_to_delete = []

        # Gather all files matching the specified patterns
        for pattern in file_patterns:
            files_to_delete.extend(glob.glob(os.path.join(WORKING_DIR, pattern)))

        # Loop through and delete each JSON file
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        rag.insert(text_content.decode('utf-8'))



# Display chat messages
for message in st.session_state.messages:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        

        

# Main chat interface
if prompt := st.chat_input("How can I help with your research?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        message_placeholder = st.empty()
        full_response = ""
        print(prompt)
        for response in rag.query(prompt, param=QueryParam(mode="hybrid")):
            
            full_response += response or ""
            
            message_placeholder.markdown(full_response + "|")
            time.sleep(0.001)
        # message_placeholder.markdown(full_response + "|")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # with st.container():
    #     st.header('Dashboard Card Title')
    #     st.text('Some interesting insights')
    #     # st.line_chart(data)

# Save chat history after each interaction
save_chat_history(st.session_state.messages)
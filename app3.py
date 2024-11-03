from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
import os
import shelve
from lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete
import textract
from unstructured.partition.auto import partition
import glob
import time
from PIL import Image
import requests
from io import BytesIO
import pandas as pd

load_dotenv()

st.set_page_config(page_title="Duke ProfMatch", page_icon="📚", layout="wide")

st.title("Duke ProfMatch")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set up LightRAG
WORKING_DIR = "./data/Affiliations/"
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

# Compressing the content
df = pd.read_csv(WORKING_DIR + 'Affiliations_sheet.csv')
df[:100].to_csv(WORKING_DIR + 'Affiliations_sheet_compressed.csv', index=False)
file_path = WORKING_DIR + 'Affiliations_sheet_compressed.csv'
text_content = textract.process(file_path)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=gpt_4o_mini_complete,
    llm_model_max_async=1
)

# Load chat history from shelve file
def load_chat_history():
    with shelve.open("chat_history") as db:
        return db.get("messages", [])

# Save chat history to shelve file
def save_chat_history(messages):
    with shelve.open("chat_history") as db:
        db["messages"] = messages

# Display a professor card with an expandable profile view
def display_professor_card(name, university, research_areas, profile_image_url, bio, interests):
    with st.container():
        cols = st.columns([1, 3])

        # Display profile image
        with cols[0]:
            if profile_image_url:
                response = requests.get(profile_image_url)
                image = Image.open(BytesIO(response.content))
                st.image(image, width=100)
            else:
                st.write("No image available")

        # Display professor details
        with cols[1]:
            st.markdown(f"**{university}**")
            st.markdown(f"### Prof. {name}")
            st.markdown(f"**Research Areas:** {research_areas}")

        # Expandable "View Profile" section
        with st.expander("View Profile"):
            st.write(f"**{name}** - {university}")
            st.write(bio)
            st.write("**Research Interests**")
            for interest in interests:
                st.markdown(f"<span class='interest-tag'>{interest}</span>", unsafe_allow_html=True)
            st.button("Connect", key=f"connect_{name}")
            st.button("Request to meet", key=f"meet_{name}")

# Initialize or load chat history
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

# File uploader for resume/CV
uploaded_file = st.file_uploader('Upload your resume/cv here:', type="pdf")
if uploaded_file is not None:
    file_elements = partition(file=uploaded_file)
    processed_file = "Special embedding as 'Me': \n" + "\n".join([str(i) for i in file_elements])
    rag.insert(processed_file)

# Sidebar with a button to delete chat history
with st.sidebar:
    if st.button("Delete Chat History"):
        st.session_state.messages = []
        save_chat_history([])
    if st.button("Reload LightRAG"):
        file_patterns = ['*.json', '*.graphml']
        files_to_delete = []
        for pattern in file_patterns:
            files_to_delete.extend(glob.glob(os.path.join(WORKING_DIR, pattern)))
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
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
        professor_data = []

        # Call RAG to get response
        for response in rag.query(prompt, param=QueryParam(mode="hybrid")):
            full_response += response or ""
            message_placeholder.markdown(full_response + "|")
            time.sleep(0.001)

            # Process response to extract professor details
            try:
                response_data = eval(response)  # Only if response is in dictionary-like string format
                for prof in response_data.get("professors", []):
                    professor_data.append({
                        "name": prof["name"],
                        "university": prof["university"],
                        "research_areas": prof["research_areas"],
                        "profile_image_url": prof.get("profile_image_url"),
                        "bio": prof.get("bio", "No bio available"),
                        "interests": prof.get("interests", [])
                    })
            except Exception as e:
                print("Error processing response:", e)

        # Display professor cards based on the extracted data
        for prof in professor_data:
            display_professor_card(
                name=prof["name"],
                university=prof["university"],
                research_areas=prof["research_areas"],
                profile_image_url=prof["profile_image_url"],
                bio=prof["bio"],
                interests=prof["interests"]
            )

        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Save chat history after each interaction
save_chat_history(st.session_state.messages)

# Bottom navigation
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.button("Home", key="home")
with col2:
    st.button("Matches", key="matches")
with col3:
    st.button("Profile", key="profile")
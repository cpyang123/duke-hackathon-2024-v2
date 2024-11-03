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
from PIL import Image
import requests
from io import BytesIO
from bs4 import BeautifulSoup
import re
import json

load_dotenv()

st.title("Duke ProfMatch")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.logo("./static/duke_match2.png", size = "large")

# Set up LightRAG
WORKING_DIR = "./data/Affiliations/"
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

# Compressing the content
import pandas as pd
df = pd.read_csv(WORKING_DIR + 'Affiliations_sheet.csv')
df[:200].to_csv(WORKING_DIR + 'Affiliations_sheet_compressed.csv', index=False)
file_path = WORKING_DIR + 'Affiliations_sheet_compressed.csv'
text_content = textract.process(file_path)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=gpt_4o_mini_complete,
    llm_model_max_async=1
)

def get_profile_picture(url):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the image tag containing the profile picture
        # This depends on the website's HTML structure. 
        # You might need to adjust the selectors below.
        img_tag = soup.find('img', class_='img xs:max-w-[240px] md:max-w-full') 

        # Extract the image URL
        if img_tag:
            img_url = img_tag['src']
            try:
                response = requests.get(img_url)
                status_code = response.status_code
            except:
                status_code = 404
            if status_code == 200:
                return Image.open(BytesIO(response.content))
            else:
                return None
    else:
        return None

# Load chat history from shelve file
def load_chat_history():
    with shelve.open("chat_history") as db:
        return db.get("messages", [])

# Save chat history to shelve file
def save_chat_history(messages):
    with shelve.open("chat_history") as db:
        db["messages"] = messages

# Display a professor card
def display_professor_card(name, university, department, research_areas, profile_url):
    with st.container():
        st.markdown("---")
        cols = st.columns([1, 2])
        
        # Display profile image
        with cols[0]:
            if profile_url:
                image = get_profile_picture(profile_url)
                if image:
                    st.image(image, width=200)
                else:
                    st.image("./static/duke_devil_logo.png", width = 200)
            else:
                st.image("./static/duke_devil_logo.png", width = 200)
        
        # Display professor details
        with cols[1]:
            st.markdown(f"**{university}**")
            st.markdown(f"### Prof. {name}")
            st.markdown(f"#### Department: {department}")
            st.markdown(f"**Researches:** {research_areas}")
            st.link_button("View profile", url= profile_url if profile_url != "" else "https://scholars.duke.edu/")

# Initialize or load chat history
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()



# Sidebar with a button to delete chat history
with st.sidebar:
    st.markdown("---")
    if st.button("Delete Chat History"):
        st.session_state.messages = []
        save_chat_history([])
    if st.button("Reload LightRAG"):
        file_patterns = ['*.json', '*.graphml']
        files_to_delete = []

        # Gather all files matching the specified patterns
        for pattern in file_patterns:
            files_to_delete.extend(glob.glob(os.path.join(WORKING_DIR, pattern)))

        # Loop through and delete each JSON file
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        rag.insert(text_content.decode('utf-8'))
    # File uploader for resume/CV
    uploaded_file = st.file_uploader('Upload your resume/cv here:', type="pdf")
    if uploaded_file is not None:
        file_elements = partition(file=uploaded_file)
        processed_file = "This is 'my' profile: \n" + "\n".join([str(i) for i in file_elements])
        rag.insert(processed_file)

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

        # Call RAG to get response
        professor_data = []
        
        with st.spinner("Analyzing Professors..."):
            rag_response = rag.query(prompt, param=QueryParam(mode="hybrid"))
            
        for response in rag_response:
            full_response += response or ""
            message_placeholder.markdown(full_response + "|")
            time.sleep(0.001)

        
        sample_dict_string = """
        {"professors" : [{"name" : "Chris P. Bacon", "university": "University of Breakfast", "department" : "Department of Mathematics", "research_areas": "area", "profile_url": "https://scholars.duke.edu/person/adam.brekke"}, 
                                             {"name" : "Sun E. Sideup", "university": "University of Dinner", "department": "Department of Physics", "research_areas": "area", "profile_url": "https://scholars.duke.edu/person/adam.brekke"}]}
        """
        with st.spinner("Fetching Prof Profiles..."):
            prof_dict_string = rag.query("If the response below includes professors, fetch the data for the professors and return a string in the format of: ```json " + sample_dict_string  + "``` use empty string if there fields missing. " + rag_response, param=QueryParam(mode="hybrid"))
        # Process response to extract professor details (assuming JSON or structured format)
        try:
            response_data = json.loads(prof_dict_string[8:-3]) 
            for prof in response_data.get("professors", []):
                professor_data.append({
                    "name": prof["name"],
                    "university": prof["university"],
                    "department": prof["department"],
                    "research_areas": prof["research_areas"],
                    "profile_url": prof.get("profile_url")
                })
        except Exception as e:
            print("Error processing response:", e)
            print(prof_dict_string)
        
        # Display professor cards based on the extracted data
        for prof in professor_data:
            display_professor_card(
                name=prof["name"],
                university=prof["university"],
                department=prof["department"],
                research_areas=prof["research_areas"],
                profile_url=prof["profile_url"]
            )
        

        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Save chat history after each interaction
    save_chat_history(st.session_state.messages)

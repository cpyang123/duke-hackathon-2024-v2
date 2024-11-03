# This is the entry point
import streamlit as st

page1 = st.Page("app.py", title="Prof-Finder")
page2 = st.Page("graph_page.py", title="Duke ProfGraph")

pg = st.navigation([page1, page2], position = "hidden")

with st.sidebar:
    st.subheader("ProfMatch Tools")
    st.page_link(page1, label = page1.title)
    st.page_link(page2, label = page2.title)
    
    st.subheader("External Resources")
    st.page_link(
        page = "https://scholars.duke.edu/", label = "Scholars@Duke"
    )
    
pg.run()
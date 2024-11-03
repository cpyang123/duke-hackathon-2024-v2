![Duke ProfMatch](https://github.com/cpyang123/duke-hackathon-2024-v2/blob/main/static/duke_match2.png)

# Duke ProfMatch

This is a project built for the 2024 Duke AI Hackathon.

See modile version of the project here: https://github.com/rishabhshah13/prof_advisor_ui


## Overview
Finding the right professor for research collaboration is often challenging for students. Many struggle to identify professors whose research aligns closely with their interests, relying on time-consuming manual searches or limited recommendations. Duke ProfMatch was inspired by the need for an efficient, accessible tool to connect students with professors based on specific research interests using natural language queries.

Duke ProfMatch enables students to connect with professors whose work aligns with their specific interests. By entering research interests in everyday language, students receive a curated list of professors, each with detailed information on their research areas, publications, and contact details. Additionally, the platform offers a graph view that visualizes Duke’s academic network, representing professors, departments, schools, and research interests as interconnected nodes. This graph allows users to conduct visual searches and explore zoomed-in sections of the network, discovering other professors or related fields of interest. Duke ProfMatch thus simplifies the search process and enhances academic networking, making it more efficient and visually engaging for students.

## Using the project

### Set-up
First, set up the right environment, via
```bash
conda env create -f environment.yml
```

### Building and running the project:
Simply run the following command:
```bash
streamlit run entry_point.py
```
Streamlit will automatically create a local host, which you can access via your preferred web-browser. 


## How we built it
First, we downloaded data from [Scholars@Duke](https://scholars.duke.edu/) as CSVs. We then coaxed it into JSON format and used Graph Retrieval-Augmented Generation (Graph RAG) with OpenAI's gpt-4o-mini to build a single graph with a few thousand nodes, and stored it into a Neo4j database. We then did prompt engineering to retrieve the appropriate context from the graph, and hooked it all up to a Streamlit frontend. 

## Challenges we ran into
One key challenge was developing the Graph DB from the dataset. This required several iterations of the system prompts along with making guardrails to ensure faithful generation of the Graph DB. The second challenge was to speed up the inference - we had to ensure the graph search narrows down to a manageable sub network of the graph, since searching over several thousand nodes would be a very expensive operation. 

## Accomplishments that we're proud of
We’re proud to have created an accessible and intuitive tool that leverages AI to make academic networking easier. Successfully integrating Graph RAG and delivering personalized, accurate matches is a major achievement. The platform's ability to search across research interests, departments, schools and publications allows for a comprehensive search, that may lead to additional inspiration for untapped research areas.

## What we learned
Building Duke ProfMatch taught us about the challenges and intricacies of context-aware AI matching, especially in academic settings. We also learned the importance of balancing technical sophistication with user-friendly design, as well as the value of ongoing data maintenance to keep recommendations accurate and reliable.

## What's next for ProfMatch
Our vision for ProfMatch includes scaling the platform to other universities, adding features like keyword alerts, collaboration suggestions, and other plugins to enhance its functionality. Additionally, we aim to continuously improve AI-driven matching accuracy to make the tool even more valuable for students and faculty alike.

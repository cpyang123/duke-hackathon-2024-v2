# pages/graph_page.py
# ---
# NetworkX Graph Visualization

import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile
import random

random.seed(23)

# st.set_page_config(page_title="NetworkX Visualization")

def remove_quotes(string):
    return string.replace('"', '')

st.title("The Duke ProfGraph")
# Set up LightRAG
WORKING_DIR = "./data/JSON/"

st.logo("./static/duke_match2.png", size= 'large')

with st.sidebar:
    st.markdown("---")

# Load the NetworkX graph
G = nx.read_graphml(WORKING_DIR + "graph_chunk_entity_relation.graphml")

# Extract node types from the graph to create filter options
entity_types = set(nx.get_node_attributes(G, "entity_type").values())  # Adjust "type" to match your node attribute key
print(entity_types)

# Sidebar filter for node types
selected_types = st.sidebar.multiselect("Filter by node type", options=entity_types, default= ['"PERSON"', '"ORGANIZATION"'], format_func = remove_quotes)

# Text input for filtering by description
description_filter = st.sidebar.text_input("Filter by description (case-insensitive)")

# Extract all node IDs with entity_type of "Person"
person_nodes = [n for n, attr in G.nodes(data=True) if attr.get("entity_type") == '"PERSON"']

# Dropdown to select a specific "Person" node ID
selected_person_id = st.sidebar.selectbox("Select a Person node ID", options=["All"] + person_nodes, format_func = remove_quotes)

# Create a filtered subgraph based on the selected entity types, description filter, and selected Person ID
filtered_nodes = []
partial_filtered = []
for node, attr in G.nodes(data=True):
    # Check if node matches selected types and description filter
    if attr.get("entity_type") in selected_types:
        if description_filter.lower() in attr.get("description", "").lower():
            partial_filtered.append(node)
            # Include only nodes that match the selected Person ID or all nodes if "All" is selected
            if selected_person_id == "All" or node == selected_person_id:
                filtered_nodes.append(node)

# Create a subgraph with the filtered nodes
G_filtered = G.subgraph(partial_filtered).copy() if filtered_nodes else G

# Further filter to only include edges connected to the selected Person node (if specified)
if selected_person_id != "All":
    neighbors = list(G_filtered.neighbors(selected_person_id))
    filtered_nodes = [selected_person_id] + neighbors
    G_filtered = G_filtered.subgraph(filtered_nodes).copy()
# print(neighbors)
# Define a color mapping for each entity type
colors = {}
for entity_type in entity_types:
    colors[entity_type] = "#{:06x}".format(random.randint(0, 0xFFFFFF))  # Random color generation

# Convert NetworkX graph to Pyvis graph and apply colors by entity type
net = Network(notebook=True)
for node, attrs in G_filtered.nodes(data=True):
    entity_type = attrs.get("entity_type", "Unknown")
    color = colors.get(entity_type, "#808080")  # Default color if entity_type is missing
    description = attrs.get("description", "No description")
    net.add_node(node, color=color, title=f"{node} - {entity_type}: {description}")

# Add edges to the Pyvis graph
for source, target, attrs in G_filtered.edges(data=True):
    net.add_edge(source, target, title=f"{attrs.get('description', 'No description')}")

# net.show_buttons(filter_=['physics'])

# Save and display the interactive graph in Streamlit
with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
    path = WORKING_DIR + "temp.html"
    net.save_graph(path)

    # Display the graph in an iframe
    st.components.v1.html(open(path).read(), height=1500)
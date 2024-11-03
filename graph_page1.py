# pages/graph_page.py
# ---
# Neo4j Graph Visualization with Streamlit and Plotly (No NetworkX or Pyvis)

import streamlit as st
import plotly.graph_objs as go
from neo4j import GraphDatabase
import random

# Neo4j connection credentials
NEO4J_URI = "x"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your_password"  # replace with your actual password

# Streamlit page configuration
st.title("Neo4j Graph Visualization")

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def fetch_entire_graph():
    """Fetch all nodes and relationships from Neo4j."""
    nodes = {}
    edges = []
    
    with driver.session() as session:
        # Fetch all nodes and relationships
        query = """
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
        result = session.run(query)
        
        for record in result:
            # Process node `n`
            node_n = record["n"]
            node_id_n = node_n.id
            if node_id_n not in nodes:
                nodes[node_id_n] = {
                    "id": node_id_n,
                    "label": node_n.get("displayName", "No Name"),
                    "group": node_n.labels.pop() if node_n.labels else "Entity"
                }
            
            # Process node `m`
            node_m = record["m"]
            node_id_m = node_m.id
            if node_id_m not in nodes:
                nodes[node_id_m] = {
                    "id": node_id_m,
                    "label": node_m.get("displayName", "No Name"),
                    "group": node_m.labels.pop() if node_m.labels else "Entity"
                }
            
            # Process relationship `r`
            edge = {
                "source": node_id_n,
                "target": node_id_m,
                "relationship": record["r"].type,
                "weight": record["r"].get("weight", 1)
            }
            edges.append(edge)
            
    return list(nodes.values()), edges

def assign_random_positions(nodes):
    """Assign random positions to nodes for layout."""
    for node in nodes:
        node['x'] = random.uniform(-1, 1)
        node['y'] = random.uniform(-1, 1)
    return nodes

def plot_graph_with_plotly(nodes, edges):
    """Create a Plotly figure from nodes and edges."""
    # Create node trace
    node_x = [node['x'] for node in nodes]
    node_y = [node['y'] for node in nodes]
    node_text = [f"{node['label']} ({node['group']})" for node in nodes]
    node_ids = [node['id'] for node in nodes]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(size=10, color='skyblue', line_width=2),
        text=node_text,
        textposition="top center",
        hoverinfo='text'
    )

    # Create edge trace
    edge_x = []
    edge_y = []
    for edge in edges:
        source_node = next(node for node in nodes if node['id'] == edge['source'])
        target_node = next(node for node in nodes if node['id'] == edge['target'])
        
        edge_x += [source_node['x'], target_node['x'], None]
        edge_y += [source_node['y'], target_node['y'], None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    # Combine node and edge traces into a Plotly figure
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0, l=0, r=0, t=0),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    ))
    return fig

# Fetch the entire graph data from Neo4j
nodes, edges = fetch_entire_graph()

# Assign random positions to nodes
nodes = assign_random_positions(nodes)

# Plot the graph with Plotly
fig = plot_graph_with_plotly(nodes, edges)

# Display the Plotly figure in Streamlit
st.plotly_chart(fig, use_container_width=True)

# Close the Neo4j driver connection
driver.close()

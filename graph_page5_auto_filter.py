import streamlit as st
from neo4j import GraphDatabase
import streamlit.components.v1 as components
import json

# Neo4j connection credentials
NEO4J_URI = "neo4j+s://090406f4.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "USz2dTV07w3kfGyru-7ZBVU-xNYKah7RTaRP31DlETM"

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def fetch_node_labels():
    """Fetch distinct node labels from Neo4j."""
    with driver.session() as session:
        result = session.run("CALL db.labels()")
        labels = [record["label"] for record in result]
    return labels

def fetch_relationship_types():
    """Fetch distinct relationship types from Neo4j."""
    with driver.session() as session:
        result = session.run("CALL db.relationshipTypes()")
        relationships = [record["relationshipType"] for record in result]
    return relationships

def fetch_graph_data(label_filter=None, relationship_filter=None):
    """Fetch nodes and edges from Neo4j based on filters and return as a JSON-compatible format."""
    nodes = []
    edges = []

    with driver.session() as session:
        # Base query
        query = "MATCH (n)-[r]->(m)"
        conditions = []

        # Apply label filter if specified
        if label_filter:
            conditions.append(f"n:{label_filter} OR m:{label_filter}")

        # Apply relationship filter if specified
        if relationship_filter:
            conditions.append(f"type(r) = '{relationship_filter}'")

        # Add conditions to the query
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Complete the query
        query += " RETURN n, r, m"

        # Run the query
        result = session.run(query)

        # Process result into nodes and edges format
        for record in result:
            # Process nodes
            node_n = record["n"]
            node_m = record["m"]

            # Define a function to determine color based on label
            def get_node_color(label):
                color_map = {
                    "ABSTRACT": "#A3C4BC",
                    "AFFILIATION": "#E6A0C4",
                    "APPOINTMENT TITLE": "#6A3D9A",
                    "AWARD": "#1F78B4",
                    "AWARD TITLE": "#33A02C",
                    "COLLEGE NAME": "#B2DF8A",
                    "COMPANY": "#B15928",
                    "DEGREE": "#1F78B4",
                    "DEMOGRAPHIC CHARACTERISTIC": "#FB9A99",
                    "DEPARTMENT": "#FDBF6F",
                    "DISEASE CHARACTERISTIC": "#CAB2D6",
                    "DUKE UNIQUE ID": "#A6CEE3",
                    "EDUCATIONAL INSTITUTE": "#B2DF8A",
                    "EMAIL": "#FB9A99",
                    "EMAIL ID": "#FF69B4",
                    "EVENT TITLE": "#FDBF6F",
                    "FILM TITLE": "#FF69B4",
                    "GROUP": "#33A02C",
                    "LOCATION": "#A6CEE3",
                    "ORGANIZATION": "#1F78B4",
                    "PROFESSIONAL NAME": "#FFD700",
                    "PROFESSIONAL ORGANIZATION": "#FFB300",
                    "PROJECT TITLE": "#1F78B4",
                    "PUBLICATION TITLE": "#00CED1",
                    "RESEARCH INTERESTS": "#B2DF8A",
                    "TREATMENT": "#6A3D9A",
                    "UNKNOWN": "#D3D3D3",
                    "YEAR": "#FF69B4"
                }
                return color_map.get(label, "#0074D9")  # Default color if label not in map

            # Determine the color based on node labels
            label_n = list(node_n.labels)[0] if node_n.labels else "Unknown"
            label_m = list(node_m.labels)[0] if node_m.labels else "Unknown"
            color_n = get_node_color(label_n)
            color_m = get_node_color(label_m)

            # Append nodes with color information
            nodes.append({
                "data": {
                    "id": node_n.id,
                    "label": node_n.get("displayName", "No Name"),
                    "color": color_n
                }
            })
            nodes.append({
                "data": {
                    "id": node_m.id,
                    "label": node_m.get("displayName", "No Name"),
                    "color": color_m
                }
            })

            # Process relationship
            relationship = record["r"]
            edges.append({
                "data": {
                    "source": node_n.id,
                    "target": node_m.id,
                    "relationship": relationship.type
                }
            })

    return json.dumps({"nodes": nodes, "edges": edges})

# Fetch dynamic filters
node_labels = fetch_node_labels()
relationship_types = fetch_relationship_types()

# Streamlit Sidebar for Filters
st.sidebar.title("Graph Filters")
label_filter = st.sidebar.selectbox("Node Label Filter", options=[""] + node_labels)  # "" for no filter
relationship_filter = st.sidebar.selectbox("Relationship Type Filter", options=[""] + relationship_types)  # "" for no filter

# Fetch graph data based on filters
graph_data = fetch_graph_data(label_filter, relationship_filter)

# Render Cytoscape graph component
components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/cytoscape/dist/cytoscape.min.js"></script>
    </head>
    <body>
        <div id="cy" style="width: 100%; height: 800px;"></div>
        <script>
            var cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: {graph_data},
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'label': 'data(label)',
                            'width': 30,
                            'height': 30,
                            'background-color': 'data(color)'  // Use the color defined in the node data
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'label': 'data(relationship)',
                            'width': 2,
                            'line-color': '#B3B3B3',
                            'target-arrow-shape': 'triangle',
                            'target-arrow-color': '#B3B3B3'
                        }}
                    }}
                ],
                layout: {{
                    name: 'cose',
                    animate: true
                }}
            }});
        </script>
    </body>
    </html>
    """, height=800)

# Close Neo4j driver connection
driver.close()

import streamlit as st
from neo4j import GraphDatabase
import streamlit.components.v1 as components
import json

# Neo4j connection credentials
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your_password"

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def fetch_graph_data():
    """Fetch nodes and edges from Neo4j and return as a JSON-compatible format."""
    nodes = []
    edges = []

    with driver.session() as session:
        # Retrieve all nodes and relationships
        query = "MATCH (n)-[r]->(m) RETURN n, r, m"
        result = session.run(query)

        for record in result:
            # Process nodes
            node_n = record["n"]
            node_m = record["m"]
            nodes.append({"data": {"id": node_n.id, "label": node_n.get("displayName", "No Name")}})
            nodes.append({"data": {"id": node_m.id, "label": node_m.get("displayName", "No Name")}})

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

# Get graph data as JSON
graph_data = fetch_graph_data()

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
                            'background-color': '#0074D9'
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

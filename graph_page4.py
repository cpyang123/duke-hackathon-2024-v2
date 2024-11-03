import streamlit as st
from neo4j import GraphDatabase
import streamlit.components.v1 as components
import json

# Neo4j connection credentials
NEO4J_URI = "neo4j+s://090406f4.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "USz2dTV07w3kfGyru-7ZBVU-xNYKah7RTaRP31DlETM"

st.logo("./static/duke_match2.png", size = "large")


# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def render_graph(user_id = None, data_type = None):
    # Fetch graph data
    query = f"""
    MATCH (n() )
    OPTIONAL MATCH (n)-[r]-(m)
    WHERE m.user_id = $user_id
    RETURN n, r, m
    """
    results = driver.execute_query(query)
    
    # Prepare data for Neovis
    nodes = []
    edges = []
    for record in results:
        n = record['n']
        nodes.append({
            "id": n.element_id,
            "label": n.get('name', '') or n.get('workType', ''),
            "group": n.group
        })
        if 'r' in record and 'm' in record:
            r = record['r']
            m = record['m']
            edges.append({
                "from": n.element_id,
                "to": m.element_id,
                "label": type(r).__name__
            })
    
    # Get Neo4j connection details
    neo4j_uri = os.environ.get("NEO4J_URI")
    neo4j_user = os.environ.get("NEO4J_USERNAME")
    neo4j_password = os.environ.get("NEO4J_PASSWORD")

    # Create Neovis config
    config = {
        "containerId": f"viz",
        "neo4j": {
            "serverUrl": neo4j_uri,
            "serverUser": neo4j_user,
            "serverPassword": neo4j_password,
        },
        "visConfig": {
            "nodes": {
                "shape": "dot",
                "size": 20,
                "font": {"size": 12}
            },
            "edges": {
                "arrows": {"to": {"enabled": True}},
                "font": {"size": 10}
            },
            "physics": {
                "enabled": True,
                "solver": "forceAtlas2Based"
            }
        },
        # "labels": {
        #     data_type: {
        #         "label": "label",
        #         "group": "group",
        #     }
        # },
    }
    
    # Render the graph
    st.components.v1.html(
        f"""
        <div id="viz" style="width: 100%; height: 300px;"></div>
        <script src="https://unpkg.com/neovis.js@2.0.2"></script>
        <script>
            var viz;
            function draw() {{
                var config = {json.dumps(config)};
                viz = new NeoVis.default(config);
                viz.renderWithCypher("{query}");
            }}
            draw();
        </script>
        """,
        height=320,
    )

render_graph()
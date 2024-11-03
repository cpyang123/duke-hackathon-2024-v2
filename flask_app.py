from flask import Flask, render_template_string

app = Flask(__name__)

# HTML template with iframe
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neo4j Browser</title>
</head>
<body>
    <h1>Neo4j Browser Embedded</h1>
    <iframe src="http://localhost:7474/browser/" width="100%" height="600px"></iframe>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True)

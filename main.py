from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    g,
    flash,
    jsonify,
)

app = Flask(__name__)


@app.route('/')
def homepage():
    return render_template("/homepage.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/tracks/bahrain')
def bahrain():
    return render_template("/tracks/bahrain.html")

@app.route('/tracks/saudi-arabia')
def saudi_arabia():
    return render_template("saudi-arabia.html")

@app.route('/tracks/australia.html')
def australia():
    return render_template("australia.html")

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)

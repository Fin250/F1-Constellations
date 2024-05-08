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

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
app.secret_key = '7EDYZ8pak3Px'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

app.app_context().push()
db.create_all()

user_credentials = [
    ('user1', 'password1'),
    ('user2', 'password2'),
    ('user3', 'password3'),
    ('user4', 'password4'),
    ('user5', 'password5'),
    ('user6', 'password6'),
    ('user7', 'password7'),
    ('user8', 'password8'),
    ('user9', 'password9'),
    ('user10', 'password10')
]

for username, password in user_credentials:
    existing_user = User.query.filter_by(username=username).first()
    if not existing_user:
        new_user = User()
        new_user.username = username
        new_user.password = generate_password_hash(password)
        db.session.add(new_user)

db.session.commit()

@app.route('/')
def homepage():
    return render_template("/homepage.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and password is not None and check_password_hash(user.password, password):
            session['username'] = user.username
            return render_template('homepage.html')
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/tracks/bahrain')
def bahrain():
    return render_template("/tracks/bahrain.html")

@app.route('/tracks/saudi-arabia')
def saudi_arabia():
    return render_template("saudi-arabia.html")

@app.route('/tracks/australia.html')
def australia():
    return render_template("australia.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return render_template("homepage.html")


@app.before_request
def before_request():
    g.username = None
    if 'username' in session:
        g.username = session['username']

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

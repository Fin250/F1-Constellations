from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    Response,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from jinja2.exceptions import TemplateNotFound
from werkzeug.security import check_password_hash, generate_password_hash

# Initialise Flask instance
app = Flask(__name__)

# Alter Flask timeout
app.config['TIMEOUT'] = 600

# Configure database URI and create database instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Session key
app.secret_key = '7EDYZ8pak3Px'

# User class used for database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Push context and create database tables
app.app_context().push()
db.create_all()

# Sample credentials
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

# User table population
for username, password in user_credentials:
    existing_user = User.query.filter_by(username=username).first()
    if not existing_user:
        new_user = User()
        new_user.username = username
        new_user.password = generate_password_hash(password)
        db.session.add(new_user)

# Commit database changes
db.session.commit()

# Homepage route
@app.route('/')
def homepage():
    return render_template("/homepage.html")

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and password is not None and check_password_hash(user.password, password):
            session['username'] = user.username
            return redirect(url_for('homepage'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

# Machine learning route
@app.route('/ml/<int:roundnum>')
def get_ml_predictions(roundnum):
    round_num = int(roundnum)
    print('ML running',round_num)

    json_test = [
        {
            "round": 5,
            "1st_predicted": "sainz",
            "1st_predicted_chance": "18.76%",
            "2nd_predicted": "alonso",
            "2nd_predicted_chance": "14.79%",
            "3rd_predicted": "russell",
            "3rd_predicted_chance": "7.40%",
            "4th_predicted": "leclerc",
            "4th_predicted_chance": "5.52%",
            "5th_predicted": "gasly",
            "5th_predicted_chance": "2.70%"
        }
    ]

    return json_test

# Render individual track pages if they exist
@app.route('/tracks/<trackname>')
def tracks(trackname):
    try:
        return render_template("/tracks/"+trackname+".html")
    except TemplateNotFound:
        return render_template("/homepage.html")

# Logout route
@app.route("/logout")
def logout():
    session['username'] = None
    session.pop("username", None)
    return redirect(url_for('homepage'))

# Session handling
@app.before_request
def before_request():
    g.username = None
    if 'username' in session:
        g.username = session['username']

# Run Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

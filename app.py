from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import TextField, StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from random import randint
from flask import request, redirect
import time
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class ReferralForm(FlaskForm):
    campaign_name = TextField('Campaign Name:', validators=[InputRequired()])
    redirect_link = TextField('Redirect Link:', validators=[InputRequired()])


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

class Referral(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15))
    redirect_link = db.Column(db.String(150))
    campaign_name = db.Column(db.String(150))
    referral_link = db.Column(db.String(150))
    click_count = db.Column(db.Integer)

class Visits(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer)
    ip = db.Column(db.String(150))
    timestamp = db.Column(db.String(100))
    referrer = db.Column(db.String(100))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))

        return '<h1>Invalid username or password</h1>'
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return '<h1>New user has been created!</h1>'
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('signup.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    form = ReferralForm()
    query = db.session.query(Referral).filter_by(username=current_user.username)
    result = db.session.execute(query)
    data = result.fetchall()
    print(data)
    return render_template('dashboard.html', name=current_user.username, form=form, data = data)

@app.route('/referral', methods=['POST', 'GET'])
@login_required
def referral():
    form = ReferralForm()
    num = randint(10000,99999)
    # Make Changes Here
    generated_link = 'http://127.0.0.1:5000/ref?id=' + str(num)
    ref = Referral(username=current_user.username, campaign_name=form.campaign_name.data, redirect_link=form.redirect_link.data, referral_link = generated_link, click_count = 0)
    db.session.add(ref)
    db.session.commit()
    return render_template('referral.html', name=current_user.username, link=generated_link)

@app.route('/ref', methods=['GET'])
def ref():
    link_id = request.args.get('id')
    ref_link = generated_link = 'http://127.0.0.1:5000/ref?id=' + str(link_id)
    ref_object = db.session.query(Referral).filter_by(referral_link=ref_link).first()
    ref_object.click_count +=1
    db.session.commit()
    link =  ref_object.redirect_link


    timestamp = datetime.datetime.utcnow()
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    referrer = request.headers.get("Referer")

    visit = Visits(target_id = link_id, ip = str(ip), timestamp = str(timestamp), referrer = str(referrer))
    db.session.add(visit)
    db.session.commit()

    return redirect(link)




@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

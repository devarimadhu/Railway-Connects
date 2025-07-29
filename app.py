from flask import Flask, request, render_template, redirect, url_for, flash, session, send_file
import pymysql
import random
import os
import time
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = 'revanminiproject'

# MySQL configurations
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'db': 'railway',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Ticket:
    def __init__(self, id=None, train_name='', starting_pt='', destination='', no_of_ac_1st_class=0, no_of_ac_2nd_class=0, no_of_ac_3rd_class=0, no_of_sleeper=0, no_of_tickets=0, name='', age=0, res_no=0, status='', created_at=None):
        self.id = id
        self.train_name = train_name
        self.starting_pt = starting_pt
        self.destination = destination
        self.no_of_ac_1st_class = no_of_ac_1st_class
        self.no_of_ac_2nd_class = no_of_ac_2nd_class
        self.no_of_ac_3rd_class = no_of_ac_3rd_class
        self.no_of_sleeper = no_of_sleeper
        self.no_of_tickets = no_of_tickets
        self.name = name
        self.age = age
        self.res_no = res_no
        self.status = status
        self.created_at = created_at

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            ''' INSERT INTO tickets (train_name, starting_pt, destination, no_of_ac_1st_class, no_of_ac_2nd_class, no_of_ac_3rd_class, no_of_sleeper, no_of_tickets, name, age, res_no, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ''',
            (self.train_name, self.starting_pt, self.destination, self.no_of_ac_1st_class, self.no_of_ac_2nd_class, self.no_of_ac_3rd_class, self.no_of_sleeper, self.no_of_tickets, self.name, self.age, self.res_no, self.status)
        )
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def find_by_res_no(res_no):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' SELECT * FROM tickets WHERE res_no = %s ''', (res_no,))
        ticket = cursor.fetchone()
        cursor.close()
        conn.close()
        if ticket:
            return Ticket(**ticket)
        return None

    @staticmethod
    def cancel_ticket(res_no):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' DELETE FROM tickets WHERE res_no = %s ''', (res_no,))
        conn.commit()
        rowcount = cursor.rowcount
        cursor.close()
        conn.close()
        return rowcount > 0

class Train:
    def __init__(self, id=None, train_no=0, train_name='', starting_pt='', destination='', no_of_ac_1st_class=0, no_of_ac_2nd_class=0, no_of_ac_3rd_class=0, no_of_sleeper=0):
        self.id = id
        self.train_no = train_no
        self.train_name = train_name
        self.starting_pt = starting_pt
        self.destination = destination
        self.no_of_ac_1st_class = no_of_ac_1st_class
        self.no_of_ac_2nd_class = no_of_ac_2nd_class
        self.no_of_ac_3rd_class = no_of_ac_3rd_class
        self.no_of_sleeper = no_of_sleeper

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        if self.id:
            cursor.execute(''' UPDATE trains SET train_no=%s, train_name=%s, starting_pt=%s, destination=%s, no_of_ac_1st_class=%s, no_of_ac_2nd_class=%s, no_of_ac_3rd_class=%s, no_of_sleeper=%s WHERE id=%s ''',
                           (self.train_no, self.train_name, self.starting_pt, self.destination, self.no_of_ac_1st_class, self.no_of_ac_2nd_class, self.no_of_ac_3rd_class, self.no_of_sleeper, self.id))
        else:
            cursor.execute(''' INSERT INTO trains (train_no, train_name, starting_pt, destination, no_of_ac_1st_class, no_of_ac_2nd_class, no_of_ac_3rd_class, no_of_sleeper) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ''',
                           (self.train_no, self.train_name, self.starting_pt, self.destination, self.no_of_ac_1st_class, self.no_of_ac_2nd_class, self.no_of_ac_3rd_class, self.no_of_sleeper))
            self.id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def get_by_id(train_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' SELECT * FROM trains WHERE id = %s ''', (train_id,))
        train = cursor.fetchone()
        cursor.close()
        conn.close()
        if train:
            return Train(**train)
        return None

    @staticmethod
    def get_all_trains():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' SELECT * FROM trains ''')
        trains = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Train(**train) for train in trains]

    @staticmethod
    def delete_by_id(train_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' DELETE FROM trains WHERE id = %s ''', (train_id,))
        conn.commit()
        rowcount = cursor.rowcount
        cursor.close()
        conn.close()
        return rowcount > 0

class User(UserMixin):
    def __init__(self, id, username, password, is_admin=False):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' SELECT * FROM users WHERE id = %s ''', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            return User(user['id'], user['username'], user['password'], user['is_admin'])
        return None

    @staticmethod
    def find_by_username(username):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' SELECT * FROM users WHERE username = %s ''', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            return User(user['id'], user['username'], user['password'], user['is_admin'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=25)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ComplaintForm(FlaskForm):
    complaint = TextAreaField('Complaint', validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('Submit')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reserve', methods=['GET', 'POST'])
@login_required
def reserve():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        train_name = request.form.get('train_name')
        starting_pt = request.form.get('starting_pt')
        destination = request.form.get('destination')
        no_of_ac_1st_class = int(request.form.get('no_of_ac_1st_class'))
        no_of_ac_2nd_class = int(request.form.get('no_of_ac_2nd_class'))
        no_of_ac_3rd_class = int(request.form.get('no_of_ac_3rd_class'))
        no_of_sleeper = int(request.form.get('no_of_sleeper'))

        if not name or not age or not train_name or not starting_pt or not destination:
            flash('All fields are required!', 'error')
            return redirect(url_for('reserve'))

        no_of_tickets = no_of_ac_1st_class + no_of_ac_2nd_class + no_of_ac_3rd_class + no_of_sleeper

        ticket = Ticket(
            name=name,
            age=int(age),
            train_name=train_name,
            starting_pt=starting_pt,
            destination=destination,
            no_of_ac_1st_class=no_of_ac_1st_class,
            no_of_ac_2nd_class=no_of_ac_2nd_class,
            no_of_ac_3rd_class=no_of_ac_3rd_class,
            no_of_sleeper=no_of_sleeper,
            no_of_tickets=no_of_tickets,
            res_no=random.randint(10000, 99999),
            status="RESERVED"
        )
        ticket.save()

        # Generate the ticket PDF
        pdf_filename = f"ticket_{ticket.res_no}.pdf"
        generate_ticket_pdf(ticket, pdf_filename)

        flash("Ticket reserved successfully. Your reservation number is {}".format(ticket.res_no), 'success')
        return send_file(pdf_filename, as_attachment=True)

    trains = Train.get_all_trains()
    return render_template('reserve.html', trains=trains)

@app.route('/success')
@login_required
def success():
    return render_template('success.html')

@app.route('/status', methods=['GET', 'POST'])
@login_required
def status():
    if request.method == 'POST':
        res_no = int(request.form['res_no'])
        ticket = Ticket.find_by_res_no(res_no)
        if ticket:
            return render_template('status.html', ticket=ticket)
        else:
            flash("No records found.")
            return redirect(url_for('index'))

    return render_template('status_form.html')

@app.route('/cancel', methods=['GET', 'POST'])
@login_required
def cancel():
    if request.method == 'POST':
        res_no = int(request.form['res_no'])
        found = Ticket.cancel_ticket(res_no)
        if found:
            flash("Ticket cancelled successfully.")
        else:
            flash("No such reservation number found.")
        return redirect(url_for('index'))

    return render_template('cancel_form.html')

@app.route('/trains', methods=['GET', 'POST'])
@login_required
def trains():
    if not current_user.is_admin:
        flash("You do not have permission to update train details.")
        return redirect(url_for('view_trains'))

    if request.method == 'POST':
        train_id = request.form.get('train_id')
        if train_id:
            # Update existing train details
            train = Train.get_by_id(train_id)
            train.train_name = request.form['train_name'].upper()
            train.train_no = int(request.form['train_no'])
            train.starting_pt = request.form['starting_pt']
            train.destination = request.form['destination']
            train.no_of_ac_1st_class = int(request.form['no_of_ac_1st_class'])
            train.no_of_ac_2nd_class = int(request.form['no_of_ac_2nd_class'])
            train.no_of_ac_3rd_class = int(request.form['no_of_ac_3rd_class'])
            train.no_of_sleeper = int(request.form['no_of_sleeper'])
            train.save()
            flash("Train details updated successfully.")
        else:
            # Add a new train
            train = Train(
                train_name=request.form['train_name'].upper(),
                train_no=int(request.form['train_no']),
                starting_pt=request.form['starting_pt'],
                destination=request.form['destination'],
                no_of_ac_1st_class=int(request.form['no_of_ac_1st_class']),
                no_of_ac_2nd_class=int(request.form['no_of_ac_2nd_class']),
                no_of_ac_3rd_class=int(request.form['no_of_ac_3rd_class']),
                no_of_sleeper=int(request.form['no_of_sleeper'])
            )
            train.save()
            flash("Train added successfully.")
        return redirect(url_for('view_trains'))

    train_id = request.args.get('train_id')
    train = Train.get_by_id(train_id) if train_id else None
    return render_template('train_form.html', train=train)

@app.route('/view_trains')
@login_required
def view_trains():
    trains = Train.get_all_trains()
    return render_template('view_trains.html', trains=trains)

@app.route('/delete_train/<int:train_id>', methods=['POST'])
@login_required
def delete_train(train_id):
    if not current_user.is_admin:
        flash("You do not have permission to delete trains.")
        return redirect(url_for('view_trains'))

    if Train.delete_by_id(train_id):
        flash("Train deleted successfully.")
    else:
        flash("Failed to delete train.")
    return redirect(url_for('view_trains'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/complaint', methods=['GET', 'POST'])
@login_required
def complaint():
    form = ComplaintForm()
    if form.validate_on_submit():
        complaint_text = form.complaint.data
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' INSERT INTO complaints (user_id, complaint) VALUES (%s, %s) ''', (current_user.id, complaint_text))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Complaint submitted successfully.')
        return redirect(url_for('index'))
    return render_template('complaint.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = generate_password_hash(form.password.data)
        is_admin = False  # Set this to True for admin users
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s) ''', (username, password, is_admin))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_username(form.username.data)
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. If you do not have an account, please register.')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

def generate_ticket_pdf(ticket, filename):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, "Railway Reservation System")
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, f"PNR Number: {ticket.res_no}")
    c.drawString(50, 680, f"Passenger Name: {ticket.name}")
    c.drawString(50, 660, f"Age: {ticket.age}")
    c.drawString(50, 640, f"Train Name: {ticket.train_name}")
    c.drawString(50, 630, f"Source: {ticket.starting_pt}")
    c.drawString(50, 620, f"Destination: {ticket.destination}")
    c.drawString(50, 600, f"Number of AC 1st Class Seats: {ticket.no_of_ac_1st_class}")
    c.drawString(50, 580, f"Number of AC 2nd Class Seats: {ticket.no_of_ac_2nd_class}")
    c.drawString(50, 560, f"Number of AC 3rd Class Seats: {ticket.no_of_ac_3rd_class}")
    c.drawString(50, 540, f"Number of Sleeper Seats: {ticket.no_of_sleeper}")
    c.drawString(50, 520, f"Total Tickets: {ticket.no_of_tickets}")
    c.drawString(50, 500, f"Status: {ticket.status}")
    c.drawString(50, 480, "Thank you for choosing our service!")
    c.save()

if __name__ == '__main__':
    app.run(debug=True)
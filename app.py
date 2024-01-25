import flask_login
from flask import Flask, render_template, url_for, redirect, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateTimeField
from wtforms.validators import InputRequired, Length, ValidationError
from flask import request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://workshop:Dupsko1234@workshop.mysql.database.azure.com/workshop"
app.config['SECRET_KEY'] = 'supersecret'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return Customer.query.get(int(user_id))


class Customer(db.Model, UserMixin):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    contact_info = db.Column(db.String(100))
    transactions = db.relationship('Transaction', backref='customer', lazy=True)


class Vehicle(db.Model):
    __tablename__ = "vehicles"
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50))
    model = db.Column(db.String(50))
    year = db.Column(db.Integer)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    services = db.relationship('Service', backref='vehicle', lazy=True)


class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)


class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    status = db.Column(db.String(20))
    scheduled_time = db.Column(db.DateTime)
    service_history = db.relationship('ServiceHistory', backref='service', lazy=True)
    external_notifications = db.relationship('ExternalNotification', backref='service', lazy=True)


class ServiceHistory(db.Model):
    __tablename__ = "service_history"
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    description = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime)


class ExternalNotification(db.Model):
    __tablename__ = "external_notifications"
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    message = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime)


class RegisterForm(FlaskForm):
    name = StringField(validators=[
        InputRequired(), Length(min=4, max=50)], render_kw={"placeholder": "Imię i nazwisko"})

    contact_info = StringField(render_kw={"placeholder": "Informacje kontaktowe"})

    submit = SubmitField('Zarejestruj się')

    def validate_name(self, name):
        existing_customer_name = Customer.query.filter_by(
            name=name.data).first()
        if existing_customer_name:
            raise ValidationError(
                'That customer already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    name = StringField(validators=[
        InputRequired(), Length(min=0, max=50)], render_kw={"placeholder": "Imię i nazwisko"})

    submit = SubmitField('Zaloguj się')


class ServiceForm(FlaskForm):
    vehicle = SelectField('Pojazd', coerce=int)
    description = StringField(validators=[
        InputRequired(), Length(min=0, max=200)], render_kw={"placeholder": "Opis usługi"})
    scheduled_time = DateTimeField('Zaplanowany czas', format='%Y-%m-%dT%H:%M')

    submit = SubmitField('Zaplanuj usługę')


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        customer = Customer.query.filter_by(name=form.name.data).first()
        if customer:
            login_user(customer)
            return redirect(url_for('dashboard'))
        else:
            flash("Nieprawidłowe dane logowania", "warning")
    return render_template('login.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    appointments = Service.query.filter_by(status='Scheduled').all()
    return render_template('dashboard.html', appointments=appointments)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    customer_in_form = form.name.data
    customers = []
    try:
        customers = db.session.execute(
            "select name from customers where name = '" + customer_in_form + "'").all()
    except:
        print("Coś poszło nie tak...")
    if form.name.data != None:
        if len(customers) == 0:
            if form.validate_on_submit():
                new_customer = Customer(name=form.name.data, contact_info=form.contact_info.data)
                db.session.add(new_customer)
                db.session.commit()
                return redirect(url_for('login'))
        else:
            flash("Taki klient już istnieje w naszej bazie", "warning")
    return render_template('register.html', form=form)


@app.route('/appointments')
@login_required
def appointments():
    appointments = Service.query.filter_by(status='Scheduled').all()
    return render_template('appointments.html', appointments=appointments)


@app.route('/schedule_service', methods=['GET', 'POST'])
@login_required
def schedule_service():
    form = ServiceForm()
    form.vehicle.choices = [(vehicle.id, f"{vehicle.make} {vehicle.model} ({vehicle.year})") for vehicle in
                            Vehicle.query.all()]

    if form.validate_on_submit():
        vehicle_id = form.vehicle.data
        description = form.description.data
        scheduled_time = form.scheduled_time.data

        new_service = Service(description=description, vehicle_id=vehicle_id, status='Scheduled',
                             scheduled_time=scheduled_time)
        db.session.add(new_service)
        db.session.commit()
        flash('Usługa została zaplanowana', 'success')
        return redirect(url_for('appointments'))

    return render_template('schedule_service.html', form=form)


@app.route("/service_history/<service_id>")
@login_required
def service_history(service_id):
    history_entries = ServiceHistory.query.filter_by(service_id=service_id).all()
    return render_template('service_history.html', history_entries=history_entries)


@app.route("/external_notifications/<service_id>")
@login_required
def external_notifications(service_id):
    notifications = ExternalNotification.query.filter_by(service_id=service_id).all()
    return render_template('external_notifications.html', notifications=notifications)


@app.route("/update_service_status/<service_id>/<new_status>")
@login_required
def update_service_status(service_id, new_status):
    service = Service.query.get(service_id)
    if service:
        service.status = new_status
        db.session.commit()
        flash('Status usługi został zaktualizowany', 'success')
    else:
        flash('Usługa nie została znaleziona', 'danger')
    return redirect(request.referrer)

if __name__ == "__main__":
    app.run(debug=True)

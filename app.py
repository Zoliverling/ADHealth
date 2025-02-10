from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diabetes_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time_glucose = db.Column(db.DateTime, nullable=True)
    time_insulin = db.Column(db.DateTime, nullable=True)
    time_bp = db.Column(db.DateTime, nullable=True)
    glucose_level = db.Column(db.Float, nullable=True)
    insulin_units = db.Column(db.Float, nullable=True)
    systolic_bp = db.Column(db.Integer, nullable=True)
    diastolic_bp = db.Column(db.Integer, nullable=True)
    carbs = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)

def get_or_create_entry(entry_date):
    entry = Entry.query.filter_by(date=entry_date).first()
    if not entry:
        entry = Entry(date=entry_date)
        db.session.add(entry)
        db.session.commit()
    return entry

def generate_glucose_insight(glucose):
    if glucose is None:
        return None
    if glucose > 180:
        return "Your glucose level is above target range (>180 mg/dL). Consider adjusting insulin dose or reducing carb intake. If this persists, consult your healthcare provider."
    elif glucose < 70:
        return "Your glucose level is below target range (<70 mg/dL). Please consume 15-20g of fast-acting carbohydrates and recheck in 15 minutes."
    else:
        return "Your glucose level is within the target range (70-180 mg/dL). Keep up the good work!"

def generate_insulin_insight(insulin, glucose=None):
    if insulin is None:
        return None
    insight = f"You've taken {insulin} units of insulin. "
    if glucose and glucose > 180:
        insight += "Since your glucose is high, ensure you're using the correct insulin-to-carb ratio."
    elif glucose and glucose < 70:
        insight += "Monitor closely for low blood sugar in the next few hours."
    return insight

def generate_bp_insight(systolic, diastolic):
    if systolic is None or diastolic is None:
        return None
    if systolic > 130 or diastolic > 80:
        return f"Blood pressure {systolic}/{diastolic} is elevated. Consider lifestyle modifications like reducing salt intake and increasing physical activity."
    else:
        return f"Blood pressure {systolic}/{diastolic} is within normal range. Great job maintaining healthy blood pressure!"

@app.route('/')
def index():
    today = date.today()
    entry = get_or_create_entry(today)
    
    glucose_insight = generate_glucose_insight(entry.glucose_level)
    insulin_insight = generate_insulin_insight(entry.insulin_units, entry.glucose_level)
    bp_insight = generate_bp_insight(entry.systolic_bp, entry.diastolic_bp)
    
    recent_entries = Entry.query.order_by(Entry.date.desc()).limit(7).all()
    
    return render_template('index.html', 
                         entry=entry,
                         recent_entries=recent_entries,
                         glucose_insight=glucose_insight,
                         insulin_insight=insulin_insight,
                         bp_insight=bp_insight)

@app.route('/update/<metric>', methods=['POST'])
def update_metric(metric):
    today = date.today()
    entry = get_or_create_entry(today)
    current_time = datetime.now()
    
    if metric == 'glucose':
        entry.glucose_level = float(request.form['glucose_level'])
        entry.time_glucose = current_time
        insight = generate_glucose_insight(entry.glucose_level)
    elif metric == 'insulin':
        entry.insulin_units = float(request.form['insulin_units'])
        entry.time_insulin = current_time
        insight = generate_insulin_insight(entry.insulin_units, entry.glucose_level)
    elif metric == 'bp':
        entry.systolic_bp = int(request.form['systolic_bp'])
        entry.diastolic_bp = int(request.form['diastolic_bp'])
        entry.time_bp = current_time
        insight = generate_bp_insight(entry.systolic_bp, entry.diastolic_bp)
    
    db.session.commit()
    return jsonify({'insight': insight})

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/daily_data')
def daily_data():
    entries = Entry.query.order_by(Entry.date.desc()).all()
    return render_template('daily_data.html', entries=entries)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
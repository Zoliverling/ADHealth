from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from sqlalchemy import func
from rag_system.utils.interface import DiabetesInsightInterface
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diabetes_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize RAG system once for the entire application
insight_interface = DiabetesInsightInterface()

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

def generate_insights_for_metrics(metrics):
    """Helper function to generate insights from metrics"""
    try:
        return insight_interface.get_insights(metrics)
    except Exception as e:
        app.logger.error(f"Error generating insights: {str(e)}")
        return {
            'glucose': "Unable to generate insight at this time.",
            'insulin': "Unable to generate insight at this time.",
            'blood_pressure': "Unable to generate insight at this time."
        }

def calculate_averages(entries):
    """Calculate averages for glucose and insulin from entries"""
    glucose_values = [e.glucose_level for e in entries if e.glucose_level is not None]
    insulin_values = [e.insulin_units for e in entries if e.insulin_units is not None]
    
    return {
        'glucose_avg': round(sum(glucose_values) / len(glucose_values), 1) if glucose_values else None,
        'insulin_avg': round(sum(insulin_values) / len(insulin_values), 1) if insulin_values else None
    }

@app.route('/')
def index():
    today = date.today()
    entry = get_or_create_entry(today)
    
    # Prepare metrics for RAG system
    metrics = {
        'glucose_level': entry.glucose_level,
        'insulin_units': entry.insulin_units,
        'systolic_bp': entry.systolic_bp,
        'diastolic_bp': entry.diastolic_bp,
        'carbs': entry.carbs
    }
    
    insights = generate_insights_for_metrics(metrics)
    recent_entries = Entry.query.order_by(Entry.date.desc()).limit(7).all()
    
    return render_template('index.html', 
                         entry=entry,
                         recent_entries=recent_entries,
                         glucose_insight=insights.get('glucose'),
                         insulin_insight=insights.get('insulin'),
                         bp_insight=insights.get('blood_pressure'))

@app.route('/update/<metric>', methods=['POST'])
def update_metric(metric):
    today = date.today()
    entry = get_or_create_entry(today)
    current_time = datetime.now()
    
    try:
        if metric == 'glucose':
            entry.glucose_level = float(request.form['glucose_level'])
            entry.time_glucose = current_time
        elif metric == 'insulin':
            entry.insulin_units = float(request.form['insulin_units'])
            entry.time_insulin = current_time
        elif metric == 'bp':
            entry.systolic_bp = int(request.form['systolic_bp'])
            entry.diastolic_bp = int(request.form['diastolic_bp'])
            entry.time_bp = current_time
        elif metric == 'carbs':
            entry.carbs = int(request.form['carbs'])
        
        db.session.commit()
        
        # Generate new insights using RAG
        metrics = {
            'glucose_level': entry.glucose_level,
            'insulin_units': entry.insulin_units,
            'systolic_bp': entry.systolic_bp,
            'diastolic_bp': entry.diastolic_bp,
            'carbs': entry.carbs
        }
        
        insights = generate_insights_for_metrics(metrics)
        insight = None
        if metric == 'glucose':
            insight = insights.get('glucose')
        elif metric == 'insulin':
            insight = insights.get('insulin')
        elif metric == 'bp':
            insight = insights.get('blood_pressure')
        
        return jsonify({'insight': insight, 'success': True})
    
    except Exception as e:
        app.logger.error(f"Error updating {metric}: {str(e)}")
        return jsonify({
            'insight': f"Error updating {metric}. Please try again.",
            'success': False
        }), 400

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/daily_data')
def daily_data():
    period = request.args.get('period', 'week')
    today = date.today()
    
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'quarter':
        start_date = today - timedelta(days=90)
    else:
        start_date = today - timedelta(days=7)  # default to week
    
    entries = Entry.query.filter(
        Entry.date >= start_date
    ).order_by(Entry.date.desc()).all()
    
    averages = calculate_averages(entries)
    
    return render_template('daily_data.html', 
                         entries=entries, 
                         current_period=period,
                         averages=averages)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Pre-initialize the RAG system's vector store
        try:
            insight_interface.rag_system.kb_processor.initialize_vector_store()
            app.logger.info("RAG system initialized successfully")
        except Exception as e:
            app.logger.error(f"Error initializing RAG system: {str(e)}")
    
    app.run(debug=True, port=5001)
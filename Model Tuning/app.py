from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from sqlalchemy import func
from rag_system.utils.multimodal_interface import DiabetesMultimodalInterface
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import base64

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diabetes_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default-dev-key')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Initialize multimodal RAG system once for the entire application
insight_interface = DiabetesMultimodalInterface()

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

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(255), nullable=True)

class PromptTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt_category = db.Column(db.String(50), nullable=False)
    prompt_text = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    user_feedback = db.Column(db.Integer, nullable=True)  # 1-5 rating
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(255), nullable=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_or_create_entry(entry_date):
    entry = Entry.query.filter_by(date=entry_date).first()
    if not entry:
        entry = Entry(date=entry_date)
        db.session.add(entry)
        db.session.commit()
    return entry

def generate_insights_for_metrics(metrics, image_path=None):
    """Helper function to generate insights from metrics"""
    try:
        return insight_interface.get_insights(metrics, image_path)
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
    """Home page with introduction to the diabetes management system"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard for health tracking"""
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
    
    return render_template('dashboard.html', 
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
        
        # Check if an image was uploaded
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(image_path)
        
        insights = generate_insights_for_metrics(metrics, image_path)
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

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        message = request.form.get('message')
        image = request.files.get('image')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        try:
            # Process image if provided
            image_path = None
            if image:
                # Save the image temporarily
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image.filename))
                image.save(image_path)
            
            # Get recent entries for context
            recent_entries = Entry.query.order_by(Entry.date.desc()).limit(7).all()
            
            # Format entries for context
            entries_context = []
            for entry in recent_entries:
                entry_data = {
                    'date': entry.date.strftime('%Y-%m-%d'),
                    'glucose': entry.glucose_level,
                    'insulin': entry.insulin_units,
                    'bp': f"{entry.systolic_bp}/{entry.diastolic_bp}" if entry.systolic_bp and entry.diastolic_bp else None,
                    'carbs': entry.carbs
                }
                entries_context.append(entry_data)
            
            # Generate response using the multimodal interface
            response_dict = insight_interface.get_chat_response(message, entries_context, image_path)
            
            # Extract response components
            response_text = response_dict.get('response', '')
            sources = response_dict.get('sources', [])
            confidence = response_dict.get('confidence', 0)
            
            # Store in database
            chat_entry = Chat(
                message=message,
                response=response_text,  # Store only the text, not the entire dictionary
                image_path=image_path
            )
            db.session.add(chat_entry)
            db.session.commit()
            
            # Clean up temporary image file
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
            
            return jsonify({
                'response': response_text,
                'sources': sources,
                'confidence': confidence
            })
        except Exception as e:
            app.logger.error(f"Error processing chat message: {str(e)}")
            return jsonify({'error': 'Unable to process your message at this time'}), 500
    
    # GET request - display chat history
    chats = Chat.query.order_by(Chat.timestamp.desc()).limit(10).all()
    return render_template('chat.html', chats=chats)

@app.route('/prompt-testing', methods=['GET', 'POST'])
def prompt_testing():
    """Page for developing and testing prompts"""
    if request.method == 'GET':
        # Get sample prompts from the text file
        prompts = {}
        try:
            with open('AI_promt_questions.txt', 'r') as f:
                current_category = None
                for line in f:
                    line = line.strip()
                    if '👨‍⚕️' in line or '🔵' in line or '🟢' in line or '🟡' in line or '🤰' in line or '🍽️' in line or '💪' in line or '😴' in line:
                        # Extract category name without emoji
                        current_category = line.split('Prompts')[0].strip()
                        # Remove emoji from category name
                        for emoji in ['👨‍⚕️', '🔵', '🟢', '🟡', '🤰', '🍽️', '💪', '😴']:
                            current_category = current_category.replace(emoji, '').strip()
                        prompts[current_category] = []
                    elif line.startswith('"') and line.endswith('"') and current_category:
                        prompts[current_category].append(line.strip('"'))
        except Exception as e:
            app.logger.error(f"Error reading prompt file: {str(e)}")
            # Provide default categories if file reading fails
            prompts = {
                "Doctor-Related": ["What kind of data will my doctor be interested in?", "Generate a report for my next checkup."],
                "Type 1 Diabetes": ["How accurate is my CGM compared to my regular meter?", "When is my CGM most likely to give a false alarm?"],
                "Type 2 Diabetes": ["How do different meals affect my fasting glucose?", "Predict my A1c based on my data."],
                "Prediabetes": ["Am I trending toward diabetes?", "Which habits seem to improve my glucose the most?"],
                "Pregnancy & Gestational Diabetes": ["How do my glucose levels compare to pregnancy-safe targets?", "What meals seem to be the best for stable blood sugar during pregnancy?"],
                "Nutrition & Meal Insights": ["Which foods cause my biggest glucose spikes?", "How long after eating does my glucose peak?"],
                "Exercise & Activity": ["How does my glucose respond to cardio vs. strength training?", "How long after working out does my glucose return to normal?"],
                "Sleep & Wellness": ["How does sleep duration affect my fasting glucose?", "Do I see higher glucose readings after bad sleep?"]
            }
        
        # Get recent tests
        recent_tests = PromptTest.query.order_by(PromptTest.timestamp.desc()).limit(10).all()
        
        return render_template('prompt_testing.html', prompts=prompts, recent_tests=recent_tests)
    
    # Handle POST request for testing a prompt
    prompt_category = request.form.get('category')
    prompt_text = request.form.get('prompt')
    
    if not prompt_text:
        flash('Please provide a prompt to test.')
        return redirect(url_for('prompt_testing'))
    
    try:
        # Check if an image was uploaded
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(image_path)
        
        # Get recent entries for context
        recent_entries = Entry.query.order_by(Entry.date.desc()).limit(7).all()
        
        # Format entries for context
        entries_context = []
        for entry in recent_entries:
            entry_data = {
                'date': entry.date.strftime('%Y-%m-%d'),
                'glucose': entry.glucose_level,
                'insulin': entry.insulin_units,
                'bp': f"{entry.systolic_bp}/{entry.diastolic_bp}" if entry.systolic_bp and entry.diastolic_bp else None,
                'carbs': entry.carbs
            }
            entries_context.append(entry_data)
        
        # Generate response
        response_dict = insight_interface.get_chat_response(prompt_text, entries_context, image_path)
        
        # Extract just the response text for database storage
        response_text = response_dict.get('response', '')
        
        # Store test in database
        test = PromptTest(
            prompt_category=prompt_category,
            prompt_text=prompt_text,
            response=response_text,  # Store only the text, not the entire dictionary
            image_path=image_path
        )
        db.session.add(test)
        db.session.commit()
        
        return jsonify({
            'response': response_dict.get('response', ''),
            'sources': response_dict.get('sources', []),
            'confidence': response_dict.get('confidence', 0),
            'test_id': test.id
        })
    
    except Exception as e:
        app.logger.error(f"Error in prompt testing: {str(e)}")
        return jsonify({
            'error': 'Unable to process your prompt at this time.'
        }), 500

@app.route('/rate-prompt/<int:test_id>', methods=['POST'])
def rate_prompt(test_id):
    """Rate a prompt test"""
    test = PromptTest.query.get_or_404(test_id)
    rating = request.form.get('rating')
    
    if rating and rating.isdigit() and 1 <= int(rating) <= 5:
        test.user_feedback = int(rating)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid rating'}), 400

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
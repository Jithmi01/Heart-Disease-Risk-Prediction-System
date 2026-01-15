from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_pymongo import PyMongo
from config import Config
import bcrypt
import jwt
import datetime
import joblib
import numpy as np
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from bson import ObjectId
import os

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# MongoDB setup
mongo = PyMongo(app)
db = mongo.db

# Load ML models
try:
    model = joblib.load('models/heart_disease_model.pkl')
    scaler = joblib.load('models/scaler.pkl')
    print("✅ Models loaded successfully")
except Exception as e:
    print(f"❌ Error loading models: {e}")
    model = None
    scaler = None

# Feature columns (matching training data)
FEATURE_COLUMNS = [
    'age', 'sex', 'resting_blood_pressure', 'cholestoral',
    'Max_heart_rate', 'exercise_induced_angina',
    'chest_pain_type_atypical_angina',
    'chest_pain_type_non_anginal_pain',
    'chest_pain_type_typical_angina'
]

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        # Check if user exists
        if db.users.find_one({'email': data['email']}):
            return jsonify({'error': 'User already exists'}), 400
        
        # Hash password
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user = {
            'name': data['name'],
            'email': data['email'],
            'password': hashed_password,
            'created_at': datetime.datetime.utcnow()
        }
        
        db.users.insert_one(user)
        
        return jsonify({'message': 'User registered successfully'}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        user = db.users.find_one({'email': data['email']})
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
            # Generate JWT token
            token = jwt.encode({
                'user_id': str(user['_id']),
                'email': user['email'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }, app.config['JWT_SECRET'], algorithm='HS256')
            
            return jsonify({
                'token': token,
                'user': {
                    'id': str(user['_id']),
                    'name': user['name'],
                    'email': user['email']
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# PREDICTION ROUTE
# ==========================================

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        # Verify JWT token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        try:
            decoded = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            user_id = decoded['user_id']
        except:
            return jsonify({'error': 'Invalid token'}), 401
        
        data = request.json
        
        # Prepare input features
        patient_input = {
            'age': float(data['age']),
            'sex': 1 if data['sex'] == 'Male' else 0,
            'resting_blood_pressure': float(data['restingBP']),
            'cholestoral': float(data['cholesterol']),
            'Max_heart_rate': float(data['maxHeartRate']),
            'exercise_induced_angina': 1 if data['exerciseAngina'] == 'Yes' else 0,
            'chest_pain_type_typical_angina': 1 if data['chestPainType'] == 'Typical Angina' else 0,
            'chest_pain_type_atypical_angina': 1 if data['chestPainType'] == 'Atypical Angina' else 0,
            'chest_pain_type_non_anginal_pain': 1 if data['chestPainType'] == 'Non-anginal Pain' else 0
        }
        
        # Convert to DataFrame
        df = pd.DataFrame([patient_input])
        
        # Ensure all feature columns exist
        for col in FEATURE_COLUMNS:
            if col not in df.columns:
                df[col] = 0
        
        df = df[FEATURE_COLUMNS]
        
        # Scale features
        X_scaled = scaler.transform(df)
        
        # Predict
        prediction = int(model.predict(X_scaled)[0])
        probability = float(model.predict_proba(X_scaled)[0][1])
        
        # Get feature importance for explanation
        feature_importance = model.feature_importances_
        
        # Calculate risk factors
        risk_factors = []
        for i, (feat, imp) in enumerate(zip(FEATURE_COLUMNS, feature_importance)):
            if df[feat].values[0] != 0:  # Only show active features
                contribution = imp * 100
                risk_factors.append({
                    'factor': feat.replace('_', ' ').title(),
                    'contribution': round(contribution, 1)
                })
        
        # Sort by contribution
        risk_factors = sorted(risk_factors, key=lambda x: x['contribution'], reverse=True)[:5]
        
        # Determine risk level
        if probability >= 0.7:
            risk_level = 'High Risk'
            risk_color = '#ef4444'
        elif probability >= 0.4:
            risk_level = 'Medium Risk'
            risk_color = '#f59e0b'
        else:
            risk_level = 'Low Risk'
            risk_color = '#10b981'
        
        # Generate recommendations
        recommendations = generate_recommendations(risk_level, patient_input)
        
        # Save prediction to database
        prediction_record = {
            'user_id': user_id,
            'patient_data': data,
            'prediction': prediction,
            'probability': probability,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'created_at': datetime.datetime.utcnow()
        }
        
        result = db.predictions.insert_one(prediction_record)
        
        return jsonify({
            'prediction': prediction,
            'probability': round(probability * 100, 2),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'report_id': str(result.inserted_id)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def generate_recommendations(risk_level, patient_data):
    recommendations = {
        'immediate_action': '',
        'lifestyle': [],
        'diet': [],
        'exercise': []
    }
    
    if risk_level == 'High Risk':
        recommendations['immediate_action'] = '🚨 Consult a cardiologist immediately. Schedule an appointment within 24-48 hours.'
        recommendations['lifestyle'] = [
            'Monitor blood pressure daily',
            'Avoid strenuous physical activities until cleared by doctor',
            'Manage stress through meditation or yoga',
            'Ensure 7-8 hours of quality sleep'
        ]
        recommendations['diet'] = [
            'Reduce sodium intake to less than 1500mg/day',
            'Eliminate trans fats and reduce saturated fats',
            'Increase omega-3 rich foods (salmon, walnuts)',
            'Eat more leafy greens and berries',
            'Limit red meat consumption'
        ]
        recommendations['exercise'] = [
            'Consult doctor before starting any exercise',
            'Start with gentle walking (10-15 minutes)',
            'Avoid high-intensity workouts',
            'Practice breathing exercises'
        ]
    
    elif risk_level == 'Medium Risk':
        recommendations['immediate_action'] = '⚠️ Schedule a check-up with your doctor within 1-2 weeks.'
        recommendations['lifestyle'] = [
            'Monitor blood pressure regularly',
            'Reduce stress levels',
            'Quit smoking if applicable',
            'Maintain healthy weight'
        ]
        recommendations['diet'] = [
            'Follow Mediterranean diet pattern',
            'Reduce sodium to 2000mg/day',
            'Increase fiber intake (whole grains, vegetables)',
            'Limit alcohol consumption',
            'Stay hydrated (8 glasses water/day)'
        ]
        recommendations['exercise'] = [
            'Aim for 150 minutes moderate exercise/week',
            'Include cardio: walking, swimming, cycling',
            'Add strength training 2x/week',
            'Practice yoga or tai chi'
        ]
    
    else:  # Low Risk
        recommendations['immediate_action'] = '✅ Continue healthy habits. Schedule annual check-up.'
        recommendations['lifestyle'] = [
            'Maintain current healthy lifestyle',
            'Regular health screenings',
            'Manage stress effectively',
            'Ensure adequate sleep'
        ]
        recommendations['diet'] = [
            'Maintain balanced, nutritious diet',
            'Include variety of fruits and vegetables',
            'Choose whole grains over refined',
            'Limit processed foods',
            'Moderate portions'
        ]
        recommendations['exercise'] = [
            'Continue regular physical activity',
            '150-300 minutes moderate exercise/week',
            'Include strength and flexibility training',
            'Try new activities to stay motivated'
        ]
    
    # Additional recommendations based on specific factors
    if patient_data['cholestoral'] > 240:
        recommendations['diet'].append('Avoid foods high in cholesterol (egg yolks, organ meats)')
    
    if patient_data['resting_blood_pressure'] > 140:
        recommendations['lifestyle'].append('Practice DASH diet for blood pressure control')
    
    return recommendations

# ==========================================
# GET USER PREDICTIONS
# ==========================================

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        decoded = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        user_id = decoded['user_id']
        
        # Get all predictions for user
        predictions = list(db.predictions.find({'user_id': user_id}).sort('created_at', -1))
        
        # Convert ObjectId to string
        for pred in predictions:
            pred['_id'] = str(pred['_id'])
        
        return jsonify(predictions), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# GENERATE PDF REPORT
# ==========================================

@app.route('/api/generate-report/<report_id>', methods=['GET'])
def generate_report(report_id):
    try:
        # Get prediction data
        prediction = db.predictions.find_one({'_id': ObjectId(report_id)})
        if not prediction:
            return jsonify({'error': 'Report not found'}), 404
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        title = Paragraph("❤️ Heart Disease Risk Assessment Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Date
        date_text = prediction['created_at'].strftime('%B %d, %Y at %I:%M %p')
        date_para = Paragraph(f"<b>Report Generated:</b> {date_text}", styles['Normal'])
        elements.append(date_para)
        elements.append(Spacer(1, 20))
        
        # Patient Information
        elements.append(Paragraph("Patient Information", heading_style))
        patient_data = [
            ['Age', str(prediction['patient_data']['age']) + ' years'],
            ['Sex', prediction['patient_data']['sex']],
            ['Resting Blood Pressure', str(prediction['patient_data']['restingBP']) + ' mm Hg'],
            ['Cholesterol Level', str(prediction['patient_data']['cholesterol']) + ' mg/dl'],
            ['Max Heart Rate', str(prediction['patient_data']['maxHeartRate']) + ' bpm'],
            ['Chest Pain Type', prediction['patient_data']['chestPainType']],
            ['Exercise Induced Angina', prediction['patient_data']['exerciseAngina']]
        ]
        
        patient_table = Table(patient_data, colWidths=[3*inch, 3*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))
        
        elements.append(patient_table)
        elements.append(Spacer(1, 20))
        
        # Risk Assessment
        elements.append(Paragraph("Risk Assessment", heading_style))
        risk_color = prediction.get('risk_color', '#10b981')
        risk_para = Paragraph(
            f"<b>Risk Level:</b> <font color='{risk_color}'>{prediction['risk_level']}</font><br/>"
            f"<b>Probability:</b> {prediction['probability']:.1f}%",
            styles['Normal']
        )
        elements.append(risk_para)
        elements.append(Spacer(1, 20))
        
        # Risk Factors
        elements.append(Paragraph("Contributing Risk Factors", heading_style))
        risk_factors_data = [['Factor', 'Contribution']]
        for factor in prediction['risk_factors']:
            risk_factors_data.append([factor['factor'], f"{factor['contribution']}%"])
        
        risk_table = Table(risk_factors_data, colWidths=[4*inch, 2*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(risk_table)
        elements.append(Spacer(1, 20))
        
        # Recommendations
        recs = prediction['recommendations']
        
        elements.append(Paragraph("Medical Recommendations", heading_style))
        elements.append(Paragraph(f"<b>{recs['immediate_action']}</b>", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Lifestyle
        elements.append(Paragraph("<b>Lifestyle Modifications:</b>", styles['Normal']))
        for item in recs['lifestyle']:
            elements.append(Paragraph(f"• {item}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Diet
        elements.append(Paragraph("<b>Dietary Recommendations:</b>", styles['Normal']))
        for item in recs['diet']:
            elements.append(Paragraph(f"• {item}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Exercise
        elements.append(Paragraph("<b>Exercise Guidelines:</b>", styles['Normal']))
        for item in recs['exercise']:
            elements.append(Paragraph(f"• {item}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Disclaimer
        disclaimer = Paragraph(
            "<i>Disclaimer: This report is generated by an AI system and should not replace professional medical advice. "
            "Please consult with a qualified healthcare provider for proper diagnosis and treatment.</i>",
            styles['Normal']
        )
        elements.append(disclaimer)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'heart_disease_report_{report_id}.pdf'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# HEALTH CHECK
# ==========================================

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'scaler_loaded': scaler is not None
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=Config.PORT)
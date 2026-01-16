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
    'chest_pain_type_Atypical angina',
    'chest_pain_type_Non-anginal pain',
    'chest_pain_type_Typical angina'
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


# # ==========================================
# PREDICTION ROUTE - WITH PATIENT DETAILS
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
        
        # Extract patient personal details
        patient_details = {
            'name': data.get('patientName', ''),
            'address': data.get('patientAddress', ''),
            'phone': data.get('patientPhone', ''),
            'email': data.get('patientEmail', '')
        }
        
        # Prepare input features with EXACT column names from training
        patient_input = {
            'age': float(data['age']),
            'sex': 1 if data['sex'] == 'Male' else 0,
            'resting_blood_pressure': float(data['restingBP']),
            'cholestoral': float(data['cholesterol']),
            'Max_heart_rate': float(data['maxHeartRate']),
            'exercise_induced_angina': 1 if data['exerciseAngina'] == 'Yes' else 0,
            'chest_pain_type_Typical angina': 1 if data['chestPainType'] == 'Typical Angina' else 0,
            'chest_pain_type_Atypical angina': 1 if data['chestPainType'] == 'Atypical Angina' else 0,
            'chest_pain_type_Non-anginal pain': 1 if data['chestPainType'] == 'Non-anginal Pain' else 0
        }
        
        # Convert to DataFrame
        df = pd.DataFrame([patient_input])
        
        # Ensure all feature columns exist in the correct order
        for col in FEATURE_COLUMNS:
            if col not in df.columns:
                df[col] = 0
        
        # Reorder to match training
        df = df[FEATURE_COLUMNS]
        
        print("Input DataFrame:")
        print(df)
        print("\nFeature columns:", df.columns.tolist())
        
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
            if df[feat].values[0] != 0 or feat in ['age', 'sex', 'resting_blood_pressure', 'cholestoral', 'Max_heart_rate']:
                contribution = imp * 100
                # Clean up feature names for display
                display_name = feat.replace('_', ' ').replace('chest pain type ', '').title()
                risk_factors.append({
                    'factor': display_name,
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
        
        # Save prediction to database with patient details
        prediction_record = {
            'user_id': user_id,
            'patient_details': patient_details,  # Added patient details
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
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()
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
# GENERATE PDF REPORT - WITH PATIENT DETAILS
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
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=26,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=20,
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
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=8,
            spaceBefore=8
        )
        
        # Logo/Header Section
        header_text = Paragraph(
            "<b>❤️ HEART CARE MEDICAL CENTER</b><br/>"
    ,
            title_style
        )
        elements.append(header_text)
        elements.append(Spacer(1, 20))
        

        
        # Date and Report ID
        date_text = prediction['created_at'].strftime('%B %d, %Y at %I:%M %p')
        info_text = Paragraph(
            f"<b>Report ID:</b> {report_id}<br/>"
            f"<b>Date Generated:</b> {date_text}",
            styles['Normal']
        )
        elements.append(info_text)
        elements.append(Spacer(1, 20))
        
        # Horizontal line
        from reportlab.platypus import HRFlowable
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563eb')))
        elements.append(Spacer(1, 20))
        
        # Patient Personal Information
        patient_details = prediction.get('patient_details', {})
        if patient_details.get('name'):
            elements.append(Paragraph("PATIENT INFORMATION", heading_style))
            
            patient_info_data = []
            if patient_details.get('name'):
                patient_info_data.append(['Patient Name', patient_details['name']])
            if patient_details.get('address'):
                patient_info_data.append(['Address', patient_details['address']])
            if patient_details.get('phone'):
                patient_info_data.append(['Phone Number', patient_details['phone']])
            if patient_details.get('email'):
                patient_info_data.append(['Email', patient_details['email']])
            
            if patient_info_data:
                patient_info_table = Table(patient_info_data, colWidths=[2*inch, 4*inch])
                patient_info_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
                    ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f3f4f6')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.white),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ]))
                
                elements.append(patient_info_table)
                elements.append(Spacer(1, 20))
        
        # Clinical Data
        elements.append(Paragraph("CLINICAL MEASUREMENTS", heading_style))
        patient_data = [
            ['Parameter', 'Value', 'Unit'],
            ['Age', str(prediction['patient_data']['age']), 'years'],
            ['Sex', prediction['patient_data']['sex'], ''],
            ['Resting Blood Pressure', str(prediction['patient_data']['restingBP']), 'mm Hg'],
            ['Cholesterol Level', str(prediction['patient_data']['cholesterol']), 'mg/dl'],
            ['Maximum Heart Rate', str(prediction['patient_data']['maxHeartRate']), 'bpm'],
            ['Chest Pain Type', prediction['patient_data']['chestPainType'], ''],
            ['Exercise Induced Angina', prediction['patient_data']['exerciseAngina'], '']
        ]
        
        patient_table = Table(patient_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(patient_table)
        elements.append(Spacer(1, 20))
        
        # Risk Assessment - Highlighted Box
        elements.append(Paragraph("RISK ASSESSMENT RESULTS", heading_style))
        
        risk_color = prediction.get('risk_color', '#10b981')
        risk_box_data = [
            ['Risk Level', prediction['risk_level']],
            ['Risk Probability', f"{prediction['probability']:.1f}%"]
        ]
        
        risk_box = Table(risk_box_data, colWidths=[2*inch, 4*inch])
        risk_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef3c7')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor(risk_color)),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#f59e0b')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(risk_box)
        elements.append(Spacer(1, 20))
        
        # Risk Factors
        elements.append(Paragraph("CONTRIBUTING RISK FACTORS", heading_style))
        risk_factors_data = [['Risk Factor', 'Contribution (%)']]
        for factor in prediction['risk_factors']:
            risk_factors_data.append([factor['factor'], f"{factor['contribution']}%"])
        
        risk_table = Table(risk_factors_data, colWidths=[4*inch, 2*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(risk_table)
        elements.append(Spacer(1, 20))
        
        # Recommendations
        recs = prediction['recommendations']
        
        elements.append(Paragraph("MEDICAL RECOMMENDATIONS", heading_style))
        
        # Immediate Action - Highlighted
        immediate_box = Table([[recs['immediate_action']]], colWidths=[6*inch])
        box_color = '#fee2e2' if 'High Risk' in prediction['risk_level'] else '#fef3c7' if 'Medium Risk' in prediction['risk_level'] else '#d1fae5'
        immediate_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(box_color)),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor(risk_color)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        elements.append(immediate_box)
        elements.append(Spacer(1, 15))
        
        # Lifestyle
        elements.append(Paragraph("Lifestyle Modifications:", subheading_style))
        for item in recs['lifestyle']:
            elements.append(Paragraph(f"• {item}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Diet
        elements.append(Paragraph("Dietary Recommendations:", subheading_style))
        for item in recs['diet']:
            elements.append(Paragraph(f"• {item}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Exercise
        elements.append(Paragraph("Exercise Guidelines:", subheading_style))
        for item in recs['exercise']:
            elements.append(Paragraph(f"• {item}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Footer with disclaimer
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        elements.append(Spacer(1, 10))
        
        disclaimer = Paragraph(
            "<i><b>Medical Disclaimer:</b> This report is generated by an AI-powered risk assessment system "
            "and is intended for informational purposes only. It should not replace professional medical advice, "
            "diagnosis, or treatment. Always consult with a qualified healthcare provider for proper medical evaluation "
            "and personalized treatment recommendations.</i>",
            ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
        )
        elements.append(disclaimer)
        
        footer_text = Paragraph(
            "<b>Heart Care Medical Center</b> | Advanced Cardiac Assessment Division<br/>"
            "Report ID: " + report_id + " | " + date_text,
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=1, textColor=colors.grey)
        )
        elements.append(Spacer(1, 10))
        elements.append(footer_text)
        
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
        print("PDF Generation Error:", str(e))
        import traceback
        traceback.print_exc()
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
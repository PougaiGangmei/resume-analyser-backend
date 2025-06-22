from flask import Flask, request, jsonify
from flask_cors import CORS
from PyPDF2 import PdfReader
import re
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "https://your-frontend-domain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Sample job database (replace with real database in production)
JOBS_DATABASE = [
    {
        "id": 1,
        "title": "Full Stack Developer",
        "company": "TechCorp",
        "required_skills": ["javascript", "react", "node", "python"],
        "nice_to_have": ["aws", "docker"],
        "salary": "$90k-$120k",
        "experience": "2+ years"
    },
    {
        "id": 2,
        "title": "Data Engineer",
        "company": "DataSystems",
        "required_skills": ["python", "sql", "spark", "etl"],
        "nice_to_have": ["airflow", "aws"],
        "salary": "$100k-$140k",
        "experience": "3+ years"
    }
]

def extract_text_from_pdf(file):
    """Extract text content from PDF file"""
    reader = PdfReader(file)
    text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text.lower()

def extract_skills(text):
    """Identify skills from text using keyword matching"""
    skill_keywords = {
        'python': ['python', 'pandas', 'numpy'],
        'javascript': ['javascript', 'js', 'es6'],
        'react': ['react', 'reactjs'],
        'sql': ['sql', 'mysql', 'postgresql'],
        'aws': ['aws', 'amazon web services']
    }
    
    found_skills = []
    for skill, keywords in skill_keywords.items():
        if any(keyword in text for keyword in keywords):
            found_skills.append(skill)
    
    return list(set(found_skills))

@app.route('/api/parse', methods=['POST'])
def parse_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    try:
        # Save file temporarily (optional)
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)
        
        # Process file
        text = extract_text_from_pdf(file)
        skills = extract_skills(text)
        
        # Clean up
        os.remove(filepath)
        
        return jsonify({
            "success": True,
            "skills": skills,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/jobs', methods=['POST'])
def recommend_jobs():
    try:
        data = request.json
        user_skills = data.get('skills', [])
        
        recommendations = []
        for job in JOBS_DATABASE:
            required_matches = sum(1 for skill in user_skills if skill in job['required_skills'])
            nice_matches = sum(1 for skill in user_skills if skill in job['nice_to_have'])
            
            match_score = int((required_matches / len(job['required_skills'])) * 100)
            
            if match_score >= 50:  # Only show relevant jobs
                recommendations.append({
                    **job,
                    "match_score": match_score,
                    "missing_skills": [s for s in job['required_skills'] if s not in user_skills],
                    "matched_skills": [s for s in user_skills if s in job['required_skills']]
                })
        
        return jsonify({
            "success": True,
            "jobs": sorted(recommendations, key=lambda x: -x['match_score'])
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
import json
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'mock_students.json')

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form.get('role')
        if user_type == 'student':
            return redirect(url_for('student_dashboard'))
        elif user_type == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif user_type == 'mentor':
            return redirect(url_for('mentor_dashboard'))
    return render_template('login.html')

@app.route('/student')
def student_dashboard():
    # In a real app we would get the logged in student's ID
    students = load_data()
    # Mocking as if S102 (Maria) logged in to show risk alert
    current_student = next((s for s in students if s['id'] == 'S102'), None)
    return render_template('dashboard_student.html', student=current_student)

@app.route('/teacher')
def teacher_dashboard():
    students = load_data()
    return render_template('dashboard_teacher.html', students=students)

@app.route('/mentor')
def mentor_dashboard():
    students = load_data()
    return render_template('dashboard_mentor.html', students=students)

@app.route('/api/students', methods=['GET'])
def api_get_students():
    return jsonify(load_data())

if __name__ == '__main__':
    app.run(debug=True, port=5000)

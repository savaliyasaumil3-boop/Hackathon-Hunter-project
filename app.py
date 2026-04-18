import json
import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# ---------- File Paths ----------
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'TS-PS12.json')
MARKS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'internal_marks.json')
INTERVENTIONS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'interventions.json')

# ---------- Subject & Class Mapping ----------
SUBJECTS = ['Mathematics', 'Computer Science', 'Physics', 'Chemistry', 'English']
CLASSES = ['Class A', 'Class B', 'Class C', 'Class D']


def get_subject(student_id):
    return SUBJECTS[int(student_id) % len(SUBJECTS)]


def get_class(student_id):
    return CLASSES[int(student_id) % len(CLASSES)]


# ---------- Data Loaders ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def load_marks():
    if not os.path.exists(MARKS_FILE):
        return {}
    with open(MARKS_FILE, 'r') as f:
        return json.load(f)


def load_interventions():
    if not os.path.exists(INTERVENTIONS_FILE):
        return {}
    with open(INTERVENTIONS_FILE, 'r') as f:
        return json.load(f)


def save_interventions(data):
    with open(INTERVENTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


# ---------- Multi-Factor Risk Engine ----------
def calculate_risk(s, marks_entry):
    """
    Weighted risk score from 0 (safe) to 100 (critical).
    Weights: attendance 35%, assignment 25%, internal_marks 25%, lms 15%
    Returns (score: int, label: str, insights: list[str])
    """
    attendance = s.get('attendance', 50)
    assignment = s.get('assignment', 50)
    lms = s.get('lms', 50)
    internal = marks_entry.get('internal_marks', 25) if marks_entry else 25
    internal_pct = (internal / 50) * 100  # normalise to %

    # Risk contribution per factor (higher = worse)
    att_risk = max(0, 100 - attendance) * 0.35
    assign_risk = max(0, 100 - assignment) * 0.25
    internal_risk = max(0, 100 - internal_pct) * 0.25
    lms_risk = max(0, 100 - lms) * 0.15

    score = int(att_risk + assign_risk + internal_risk + lms_risk)
    score = min(score, 100)

    # Label
    if score >= 60:
        label = 'High'
    elif score >= 35:
        label = 'Medium'
    else:
        label = 'Low'

    # Explainable Insights
    factors = [
        ('Attendance', attendance, 60),
        ('Assignment Completion', assignment, 60),
        ('Internal Marks', internal_pct, 50),
        ('LMS Engagement', lms, 40),
    ]
    insights = []
    for name, val, threshold in factors:
        if val < threshold:
            insights.append(f'{name} is critically low ({val:.0f}%)')

    if not insights:
        insights.append('All metrics are within acceptable range.')

    return score, label, insights


# ---------- Before/After Improvement ----------
def get_improvement(s_id, interventions):
    """
    Compares pre-intervention snapshot with current values.
    Returns a dict with delta values, or None if no intervention.
    """
    log = interventions.get(str(s_id))
    if not log or not log.get('snapshot'):
        return None

    snap = log['snapshot']
    s = log.get('current', {})

    # If current not saved yet, generate a simulated improvement
    improvement = {
        'attendance_delta': random.randint(3, 18),
        'marks_delta': random.randint(2, 15),
        'assignment_delta': random.randint(5, 20),
        'risk_delta': random.randint(5, 25),
        'intervention_type': log.get('type', 'Counselling Session'),
        'intervention_date': log.get('date', 'N/A'),
        'notes': log.get('notes', ''),
    }
    return improvement


# ---------- Alert Engine ----------
def get_mentor_alerts(all_students, interventions):
    """Top 5 High-Risk students with no intervention logged yet."""
    alerts = []
    for s in all_students:
        if s.get('dynamic_risk_label') == 'High' and str(s['student_id']) not in interventions:
            alerts.append(s)
        if len(alerts) >= 5:
            break
    return alerts


# ---------- Main Loader ----------
def get_filtered_students(req_args, include_marks=True):
    data = load_data()
    marks_data = load_marks()
    interventions = load_interventions()

    student_id = req_args.get('student_id')
    risk_label = req_args.get('risk_label')
    subject_filter = req_args.get('subject')
    class_filter = req_args.get('class_name')

    # Filter by Student ID
    if student_id:
        try:
            data = [s for s in data if str(s.get('student_id')) == str(student_id)]
        except ValueError:
            pass

    # Filter by Class and Subject early (before enrichment loop) to save time
    if class_filter and class_filter != 'All':
        data = [s for s in data if get_class(s.get('student_id', 0)) == class_filter]

    if subject_filter and subject_filter != 'All':
        data = [s for s in data if get_subject(s.get('student_id', 0)) == subject_filter]

    enriched = []
    for s in data:
        s_id = str(s['student_id'])
        marks_entry = marks_data.get(s_id)

        # Compute dynamic multi-factor risk
        dyn_score, dyn_label, insights = calculate_risk(s, marks_entry)
        
        # Filter by risk label
        if risk_label and risk_label != 'All' and dyn_label != risk_label:
            continue

        # Add restricted marks
        if include_marks and marks_entry:
            s['internal_marks'] = marks_entry.get('internal_marks', 'N/A')
            s['mid_exam_marks'] = marks_entry.get('mid_exam_marks', 'N/A')

        s['dynamic_risk_score'] = dyn_score
        s['dynamic_risk_label'] = dyn_label
        s['insights'] = insights

        # Class and Subject mapping
        s['subject'] = get_subject(s['student_id'])
        s['class_name'] = get_class(s['student_id'])

        # Before/After intervention
        s['improvement'] = get_improvement(s['student_id'], interventions)

        enriched.append(s)

        # Break early once we have enough results to render the UI efficiently
        if len(enriched) >= 100:
            break

    return enriched


# ---------- Routes ----------
@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form.get('role')
        if user_type == 'student':
            student_id = request.form.get('student_id')
            if not student_id:
                student_id = '4'
            return redirect(url_for('student_dashboard', sid=student_id))
        elif user_type == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif user_type == 'mentor':
            return redirect(url_for('mentor_dashboard'))
    return render_template('login.html')


@app.route('/student')
def student_dashboard():
    sid = request.args.get('sid', '4')
    students = load_data()
    marks_data = load_marks()
    current_student = next((s for s in students if str(s['student_id']) == sid), None)
    if current_student:
        marks_entry = marks_data.get(sid)
        dyn_score, dyn_label, insights = calculate_risk(current_student, marks_entry)
        current_student['dynamic_risk_score'] = dyn_score
        current_student['dynamic_risk_label'] = dyn_label
        current_student['insights'] = insights
        current_student['subject'] = get_subject(current_student['student_id'])
        current_student['class_name'] = get_class(current_student['student_id'])
    return render_template('dashboard_student.html', student=current_student)


@app.route('/teacher')
def teacher_dashboard():
    students = get_filtered_students(request.args)
    return render_template(
        'dashboard_teacher.html',
        students=students,
        subjects=['All'] + SUBJECTS,
        classes=['All'] + CLASSES
    )


@app.route('/mentor')
def mentor_dashboard():
    students = get_filtered_students(request.args)
    interventions = load_interventions()
    alerts = get_mentor_alerts(students, interventions)
    return render_template(
        'dashboard_mentor.html',
        students=students,
        alerts=alerts,
        subjects=['All'] + SUBJECTS,
        classes=['All'] + CLASSES
    )


@app.route('/intervene', methods=['POST'])
def log_intervention():
    """Save an intervention record for a student."""
    data = request.get_json()
    if not data or 'student_id' not in data:
        return jsonify({'error': 'Missing student_id'}), 400

    interventions = load_interventions()
    s_id = str(data['student_id'])

    # Snapshot current student metrics for before/after comparison
    students = load_data()
    student = next((s for s in students if str(s['student_id']) == s_id), {})

    interventions[s_id] = {
        'type': data.get('type', 'Counselling Session'),
        'notes': data.get('notes', ''),
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'snapshot': {
            'attendance': student.get('attendance'),
            'marks': student.get('marks'),
            'assignment': student.get('assignment'),
            'lms': student.get('lms'),
        }
    }
    save_interventions(interventions)
    return jsonify({'success': True, 'message': f'Intervention logged for Student #{s_id}'})


@app.route('/api/students', methods=['GET'])
def api_get_students():
    return jsonify(get_filtered_students(request.args))


if __name__ == '__main__':
    app.run(debug=True, port=5000)

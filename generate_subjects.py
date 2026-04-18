import json
import random
import os

from app import SUBJECTS

data_file = os.path.join('data', 'TS-PS12.json')
output_file = os.path.join('data', 'subject_metrics.json')

def generate_subjects():
    try:
        with open(data_file, 'r') as f:
            students = json.load(f)
            
        subject_data = {}
        for s in students:
            base_att = s.get('attendance', 60)
            base_mark = s.get('marks', 60)
            base_assign = s.get('assignment', 60)
            base_lms = s.get('lms', 60)

            student_subjects = {}
            for subj in SUBJECTS:
                # Add random variance from -15 to +15 around the baseline, capped between 0 and 100
                student_subjects[subj] = {
                    'attendance': max(0, min(100, base_att + random.randint(-15, 15))),
                    'marks': max(0, min(100, base_mark + random.randint(-15, 15))),
                    'assignment': max(0, min(100, base_assign + random.randint(-15, 15))),
                    'lms': max(0, min(100, base_lms + random.randint(-15, 15)))
                }
            
            subject_data[str(s['student_id'])] = student_subjects
            
        with open(output_file, 'w') as f:
            json.dump(subject_data, f)
            
        print(f"Successfully generated {len(subject_data)} subject metric records.")
        
    except Exception as e:
        print(f"Error generation dataset: {e}")

if __name__ == "__main__":
    generate_subjects()

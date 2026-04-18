import json
import random
import os

data_file = os.path.join('data', 'TS-PS12.json')
output_file = os.path.join('data', 'internal_marks.json')

def generate_marks():
    try:
        with open(data_file, 'r') as f:
            students = json.load(f)
            
        marks_data = {}
        for s in students:
            # Generate random internal marks out of 50
            internal = random.randint(10, 50)
            
            # Generate random mid exam marks out of 30, correlation to risk_score could be added but random is fine for mock
            mid_exam = random.randint(5, 30)
            
            marks_data[str(s['student_id'])] = {
                'internal_marks': internal,
                'mid_exam_marks': mid_exam
            }
            
        with open(output_file, 'w') as f:
            json.dump(marks_data, f)
            
        print(f"Successfully generated {len(marks_data)} internal marks records.")
        
    except Exception as e:
        print(f"Error generation dataset: {e}")

if __name__ == "__main__":
    generate_marks()

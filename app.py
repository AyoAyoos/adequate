import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import current_user # Make sure you import this
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from model import predict_bloom_level
import json
from dotenv import load_dotenv
from supabase import create_client, Client
import re

from LLM.engine import GuidanceEngine

load_dotenv()

app = Flask(__name__)
app.secret_key = "a_very_secret_key_for_sessions" # Changed for security


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)


# In app.py

SKILL_LEVELS = {
    "low": [
        "Accuracy & Speed",
        "Agile",
        "Attention to Detail",
        "Basic Computer Skills",
        "Basic IT Knowledge",
        "Communication",
        "communication skills", # Standardize this
        "Computer Basics",
        "Customer Service",
        # ... add all other "low" skills here
    ],
    "medium": [
        "Advanced SQL",
        "C++ Programming",
        "CSS Flexbox", # Example
        "Database Management",
        "Git",
        "HTML/CSS/JavaScript",
        "Java",
        "JavaScript",
        "Python",
        # ... add all other "medium" skills here
    ],
    "high": [
        "AI & Machine Learning", # Example
        "Cloud Computing (AWS/Azure)",
        "Deep Learning",
        "Machine Learning Algorithms",
        "NLP Libraries",
        "System Design & Architecture",
        # ... add all other "high" skills here
    ]
}

# Add this new function to app.py

def get_skills_for_user(scores_dict):
    """
    Determines a user's AQ level from their scores and
    returns the correctly filtered list of skills.
    """
    if not scores_dict:
        return [] # Return empty list if no scores

    # 1. Get the user's total AQ score.
    #    This handles both 'testdrive' users and real users.
    total_score = scores_dict.get('total_aq_score') or scores_dict.get('aq_score', 0)
    
    # 2. Determine the AQ level (you can adjust these thresholds)
    if total_score < 140:
        level = "low"
    elif total_score < 180:
        level = "medium"
    else:
        level = "high"
    
    # 3. Get the correct skill list from your dictionary
    filtered_skills = SKILL_LEVELS.get(level, [])
    
    # 4. Return the sorted list
    return sorted(filtered_skills)

    
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "hehe"

# --- Configuration for File Uploads ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

print("--- FLASK APP STARTING: INITIALIZING GUIDANCE ENGINE ---")
# Define the paths for the engine's data files
engine_config = {
    'student_data_path': os.path.join('LLM', 'data', 'Final_Sheet - Sheet3.csv'),
    'research_paper_path': os.path.join('LLM', 'data', 'Research_Paper.pdf'),
    'faiss_index_path': os.path.join('LLM', 'embeddings', 'faiss_index')
}
guidance_engine = GuidanceEngine(config=engine_config)
print("--- GUIDANCE ENGINE INITIALIZED SUCCESSFULLY ---")




# NEW: Add the missing helper function here

def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




@app.route("/login/google")
def login_with_google():
    """
    This route starts the Google login process.
    It tells Supabase to get a login URL from Google
    and then sends the user to that URL.
    """
    # Get the URL to redirect the user to from Supabase
    auth_url = supabase.auth.sign_in_with_oauth(
       {  # <-- START of the single dictionary
            "provider": "google",
            "options": {
                "redirect_to": url_for("google_auth_callback", _external=True)
            }
        }
    )
    return redirect(auth_url.url)

@app.route("/auth/callback")
def google_auth_callback():
    """
    Google sends the user here AFTER they have successfully logged in.
    We exchange a one-time code for a real user session.
    """
    try:
        # Get the 'code' from the URL query parameters
        auth_code = request.args.get("code")
        if not auth_code:
            flash("Authentication failed: No code provided.", "danger")
            return redirect(url_for('home'))

        # Exchange the code for a user session
        session_data = supabase.auth.exchange_code_for_session({
            "auth_code": auth_code
        })
        
        # This is the logged-in user from Supabase
        user = session_data.user
        user_email = user.email

        # --- This is our main login logic ---
        # 1. Check if this email belongs to a TEACHER
        teacher_response = supabase.table('teachers').select('*').eq('email', user_email).limit(1).execute()
        
        if teacher_response.data:
            teacher = teacher_response.data[0]
            # Log them in as a teacher
            session['teacher_id'] = teacher['id']
            session['teacher_name'] = teacher['name']
            
            # Link their Supabase Auth ID to their teacher record
            supabase.table('teachers').update({'user_id': user.id}).eq('id', teacher['id']).execute()
            
            return redirect(url_for('teacher_dashboard'))

        # 2. If not a teacher, check if this email belongs to a STUDENT
        student_response = supabase.table('students').select('*').eq('email', user_email).limit(1).execute()
        
        if student_response.data:
            student = student_response.data[0]
            # Log them in as a student
            session['student_id'] = student['id']
            session['enrollment_no'] = student['enrollment_no']
            
            # Link their Supabase Auth ID to their student record
            supabase.table('students').update({'user_id': user.id}).eq('id', student['id']).execute()
            
            return redirect(url_for('student_dashboard'))

        # 3. If they are in NEITHER table, they are not registered.
        flash(f"Your email ({user_email}) is not registered. Please contact an admin.", "warning")
        return redirect(url_for('home'))

    except Exception as e:
        flash(f"An error occurred during authentication: {e}", "danger")
        return redirect(url_for('home'))
# ---------------------------
# Routes
# ---------------------------

@app.route('/')
def intro():
    """
    This is the main route that will show the animated intro page.
    It renders the intro.html template.
    """
    return render_template("intro.html")

@app.route('/home')
def home():
    """
    This route serves your original index.html page. The intro page
    will redirect to this route after its animation finishes.
    """
    return render_template("index.html")
# --- Teacher Authentication ---


"""

@app.route("/teacher/register", methods=["GET", "POST"])
def teacher_register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        subject = request.form.get("subject", "")

        # Basic validation (unchanged)
        if not name or not email or not password:
            flash("Please fill out all required fields.", "danger")
            return redirect(url_for("teacher_register"))

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("teacher_register"))

        # Hash the password before saving (unchanged)
        hashed_password = generate_password_hash(password)

        try:
            # --- NEW SUPABASE CODE ---
            # Replaces conn.execute, conn.commit, conn.close
            response = supabase.table('teachers').insert({
                "name": name,
                "email": email,
                "password": hashed_password,
                "subject": subject
            }).execute()
            # --- END OF NEW CODE ---

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("teacher_login"))
        
        except Exception as e:
            # --- NEW SUPABASE ERROR HANDLING ---
            # This catches the duplicate email error (and other errors)
            flash("Email address already registered. Please log in.", "danger")
            return redirect(url_for("teacher_register"))

    return render_template("teacher_registration.html")

#
# THIS LINE MUST HAVE ZERO INDENTATION
#
@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # --- NEW SUPABASE CODE ---
        # Replaces conn.execute and conn.close
        response = supabase.table('teachers').select('*').eq('email', email).limit(1).execute()
        # --- END OF NEW CODE ---

        teacher = None
        # --- NEW: Check if Supabase found a user ---
        if response.data:
            teacher = response.data[0] # This is the new "fetchone()"

        # This logic is now checking the Supabase 'teacher' variable
        if teacher and check_password_hash(teacher['password'], password):
            # Login successful, store teacher info in session
            session['teacher_id'] = teacher['id']
            session['teacher_name'] = teacher['name']
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return redirect(url_for('teacher_login'))

    return render_template("teacher_login.html")



@app.route("/teacher/dashboard")
def teacher_dashboard():
    # Protect the route - only logged-in teachers can access
    if 'teacher_id' in session:
        # 1. Create a dictionary to hold the teacher's data.
        #    This matches the structure the template expects (teacher.name).
        teacher_data = {
            'name': session.get('teacher_name', 'Teacher') # Using .get() is safer
        }
        
        # 2. Pass the entire dictionary to the template as the 'teacher' variable.
        return render_template("teacher_dashboard.html", teacher=teacher_data)
    
    flash("You need to be logged in to access this page.", "danger")
    return redirect(url_for('teacher_login'))



@app.route("/teacher/students")
def teacher_students():
    # Protect the route - only logged-in teachers can access
    if 'teacher_id' not in session:
        flash("You need to be logged in to access this page.", "danger")
        return redirect(url_for('teacher_login'))
    
    # Get the ID of the currently logged-in teacher
    teacher_id = session['teacher_id']
    
    # --- NEW SUPABASE CODE ---
    # Replaces conn.execute, fetchall, and conn.close
    response = supabase.table('students').select(
        'id, enrollment_no, aq_score'
    ).eq('teacher_id', teacher_id).execute()
    
    students = response.data
    # --- END OF NEW CODE ---
    
    # Render a NEW template and pass the student data to it
    return render_template("teacher_students.html", students=students)



@app.route('/teacher/logout')
def teacher_logout():
    # Remove teacher-specific data from the session
    session.pop('teacher_id', None)
    session.pop('teacher_name', None)
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('home')) # Redirect to the main home page


# ---------------------------------------------
# CORE MODEL FUNCTIONALITY ROUTE
# ---------------------------------------------
@app.route('/upload_predict', methods=['POST'])
def upload_predict():
    if 'teacher_id' not in session:
        flash("You must be logged in to access this feature.", "danger")
        return redirect(url_for('teacher_login'))

    if 'file' not in request.files:
        flash('No file part selected in the form.', "danger")
        return redirect(url_for('teacher_dashboard'))
    
    file = request.files['file']

    if file.filename == '':
        flash('No file selected.', "danger")
        return redirect(url_for('teacher_dashboard'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Ensure the uploads directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Read the uploaded file using pandas
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)

            # Validate that the 'question' column exists
            if 'question' not in df.columns:
                flash('The uploaded file must contain a column named "question".', "danger")
                return redirect(url_for('teacher_dashboard'))

            # Apply the prediction model to each question
            df['predicted_level'] = df['question'].apply(predict_bloom_level)
            
            # Convert the DataFrame into a list of dictionaries.
            results = df.to_dict(orient='records')
            
            # Render the HTML page, sending the results data directly to it.
            # No need to store in session anymore.
            return render_template('results.html', results=results)

        except Exception as e:
            flash(f"An error occurred while processing the file: {e}", "danger")
            return redirect(url_for('teacher_dashboard'))

    else:
        flash('Invalid file type. Please upload a .csv or .xlsx file.', "danger")
        return redirect(url_for('teacher_dashboard'))


# --- Placeholder Routes ---
# --- Admin Authentication Routes ---

# --- Hard-coded Admin Credentials ---


# --- Admin Authentication Routes ---

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    # If the form is submitted
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # Check if the credentials match the hard-coded values
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True  # Store login status in session
            flash('Login Successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return redirect(url_for('admin_login'))
            
    # For a GET request, just show the login page
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    # Protect this route (this part is unchanged)
    if not session.get('admin_logged_in'):
        flash('You need to be logged in to view this page.', 'warning')
        return redirect(url_for('admin_login'))

    # --- NEW SUPABASE CODE ---
    # Replaces conn = get_db_connection()

    # 1. Fetch all students
    students_response = supabase.table('students').select('enrollment_no').execute()
    students = students_response.data

    # 2. Fetch all teachers
    teachers_response = supabase.table('teachers').select('id, name').execute()
    teachers = teachers_response.data

    # Replaces conn.close() (no longer needed)
    # --- END OF NEW CODE ---
    
    # Render the new dashboard template and pass the 'students' data to it
    return render_template("admin_dashboard.html", students=students, teachers=teachers)


@app.route("/admin/logout")
def admin_logout():
    # Clear the session to log the admin out
    session.pop('admin_logged_in', None)
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('home'))


@app.route("/admin/upload", methods=["POST"])
def admin_upload_students():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    # ... (file and teacher_id checks are unchanged) ...
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('admin_dashboard'))

    teacher_id = request.form.get('teacher_id')
    if not teacher_id:
        flash('You must select a teacher to assign the students to.', 'danger')
        return redirect(url_for('admin_dashboard'))

    file = request.files['file']
    if file and allowed_file(file.filename):
        try:
            df = pd.read_excel(file)
            required_cols = ['enrollment_no', 'password']
            if not all(col in df.columns for col in required_cols):
                flash(f'Error: Excel file must have columns: {", ".join(required_cols)}', 'danger')
                return redirect(url_for('admin_dashboard'))

            # --- NEW: Build a list of students to insert ---
            students_to_insert = []
            processed_count = 0
            
            for index, row in df.iterrows():
                # ... (data extraction logic is unchanged) ...
                enrollment_no_raw = str(row.get('enrollment_no', '')).strip()
                password_value = row.get('password')
                password_raw = ""
                if pd.notna(password_value):
                    try:
                        password_raw = str(int(float(password_value)))
                    except (ValueError, TypeError):
                        password_raw = str(password_value).strip()

                if not enrollment_no_raw or not password_raw:
                    continue

                hashed_password = generate_password_hash(password_raw)
                processed_count += 1
                
                # --- NEW: Add student to our list instead of inserting ---
                students_to_insert.append({
                    'enrollment_no': enrollment_no_raw,
                    'password_hash': hashed_password,
                    'teacher_id': teacher_id
                })
            
            # --- NEW: Insert all students in one batch ---
            if students_to_insert:
                # This single command replaces the entire try/except/commit/close block
                response = supabase.table('students').insert(
                    students_to_insert,
                    on_conflict='enrollment_no',  # The column to check for duplicates
                    ignore_duplicates=True  # This is the new 'except ...: pass'
                ).execute()
                
                newly_added_count = len(response.data)
            else:
                newly_added_count = 0

            flash(f'Success! Processed {processed_count} records. Added {newly_added_count} new students.', 'success')
        
        except Exception as e:
            flash(f'An unexpected error occurred: {e}', 'danger')
    else:
        flash('Invalid file type. Please upload an .xlsx file.', 'danger')
    
    return redirect(url_for('admin_dashboard'))

    """

# --- CORRECTED STUDENT ROUTES FOR DEMO USER ---

@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        enrollment_no = request.form.get("enrollment_no")
        password = request.form.get("password")

        # --- This "testdrive" logic is unchanged. It's perfect. ---
        if enrollment_no == "testdrive" and password == "testdrive":
            session['student_id'] = 0
            session['enrollment_no'] = 'testdrive'
            # Clear any previous test data
            session.pop('test_user_scores', None)
            session.pop('test_user_report_data', None)
            session.pop('test_user_skills', None)
            flash("Logged in as a temporary test user.", "success")
            return redirect(url_for('student_dashboard'))

        # Original logic for real users (unchanged)
        if not enrollment_no or not password:
            flash("Please enter both enrollment number and password.", "danger")
            return redirect(url_for('student_login'))
        
        # --- NEW SUPABASE CODE ---
        # Replaces get_db_connection, conn.execute, and conn.close
        response = supabase.table('students').select('*').eq('enrollment_no', enrollment_no).limit(1).execute()
        
        student = None
        if response.data:
            student = response.data[0] # This is the new "fetchone()"
        # --- END OF NEW CODE ---

        # This logic is unchanged and now works with the 'student' from Supabase
        if student and check_password_hash(student['password_hash'], password):
            session['student_id'] = student['id']
            session['enrollment_no'] = student['enrollment_no']
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid enrollment number or password.', 'danger')
        
        return redirect(url_for('student_login'))

    return render_template("student_login.html")

#
# --- NEW ROUTE FOR PUBLIC STUDENT REGISTRATION ---
#
@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        enrollment_no = request.form["enrollment_no"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        
        # --- Validation ---
        if not enrollment_no or not email or not password:
            flash("Please fill out all fields.", "danger")
            return redirect(url_for("student_register"))

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("student_register"))

        hashed_password = generate_password_hash(password)
        
        # --- THIS IS THE KEY ---
        # 1. Go to your Supabase table for 'teachers'.
        # 2. Manually add a row called "Public Students".
        # 3. Get the 'id' for that row and paste it here.
        PUBLIC_TEACHER_ID = 7 # <-- CHANGE THIS ID

        try:
            response = supabase.table('students').insert({
                "enrollment_no": enrollment_no,
                "password_hash": hashed_password,
                "email": email, # The email column we added for Google Auth
                "teacher_id": PUBLIC_TEACHER_ID 
            }).execute()

            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("student_login"))
        
        except Exception as e:
            # This will catch if the email or enrollment_no is already taken
            flash("Email or Enrollment Number is already registered.", "danger")
            return redirect(url_for("student_register"))

    # Show the registration form
    return render_template("student_register.html")

@app.route("/student/dashboard")
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    
    assessment_has_been_taken = False
    # --- "testdrive" logic is unchanged ---
    if session.get('student_id') == 0:
        assessment_has_been_taken = 'test_user_scores' in session
    else:
        # --- NEW SUPABASE CODE ---
        # Replaces get_db_connection, conn.execute, and conn.close
        response = supabase.table('students').select('aq_score').eq('id', session['student_id']).limit(1).execute()
        
        if response.data:
            student_data = response.data[0] # This is the new "fetchone()"
            assessment_has_been_taken = student_data['aq_score'] is not None
        # --- END OF NEW CODE ---

    return render_template("student_dashboard.html", assessment_taken=assessment_has_been_taken)


@app.route("/student/assessment")
def student_assessment():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    return render_template("student_assessment.html")


@app.route("/student/submit_assessment", methods=["POST"])
def submit_assessment():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    # --- Score calculation is unchanged ---
    control_score = sum(int(request.form.get(f'q{i}', 0)) for i in range(1, 4))
    ownership_score = sum(int(request.form.get(f'q{i}', 0)) for i in range(4, 12))
    reach_score = sum(int(request.form.get(f'q{i}', 0)) for i in range(12, 17))
    endurance_score = sum(int(request.form.get(f'q{i}', 0)) for i in range(17, 22))
    attitude_score = sum(int(request.form.get(f'q{i}', 0)) for i in [22, 23])
    total_aq_score = (control_score + ownership_score + reach_score + endurance_score + attitude_score) * 2
    
    # --- "testdrive" logic is unchanged ---
    if session.get('student_id') == 0:
        session['test_user_scores'] = {
            'control_score': control_score, 'ownership_score': ownership_score,
            'reach_score': reach_score, 'endurance_score': endurance_score,
            'attitude_score': attitude_score, 'total_aq_score': total_aq_score
        }
    else:
        # --- NEW SUPABASE CODE ---
        # Replaces get_db_connection, conn.execute, conn.commit, and conn.close
        scores_to_update = {
            "aq_score": total_aq_score,
            "control_score": control_score,
            "ownership_score": ownership_score,
            "reach_score": reach_score,
            "endurance_score": endurance_score,
            "attitude_score": attitude_score
        }
        
        response = supabase.table('students').update(scores_to_update).eq('id', session['student_id']).execute()
        # --- END OF NEW CODE ---

    return redirect(url_for('show_assessment_results'))

@app.route("/student/assessment_results")
def show_assessment_results():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    scores = None
    # --- "testdrive" logic is unchanged ---
    if session.get('student_id') == 0:
        scores = session.get('test_user_scores')
    else:
        # --- NEW SUPABASE CODE ---
        # Replaces get_db_connection, conn.execute, fetchone, and conn.close
        # --- NEW SUPABASE CODE ---
        # Replaces get_db_connection, conn.execute, fetchone, and conn.close
        response = supabase.table('students').select(
            'aq_score, control_score, ownership_score, reach_score, endurance_score, attitude_score'
        ).eq('id', session['student_id']).limit(1).execute()
        
        if response.data:
            # response.data[0] is already the dictionary we need
            scores = response.data[0] 
        # --- END OF NEW CODE ---

    if not scores:
        flash("Could not retrieve assessment scores. Please take the assessment again.", "danger")
        return redirect(url_for('student_assessment'))

    # --- This part is unchanged ---
    # --- This is the NEW logic ---
    # Call your new function to get the *filtered* skill list
    filtered_skills = get_skills_for_user(scores)
    
    scores_json = json.dumps(scores)
    
    # Pass the new 'filtered_skills' list to the template.
    # The template (assessment_results.html) will still call it 'all_skills'
    return render_template("assessment_results.html", scores=scores, all_skills=filtered_skills)

@app.route("/student/generate_report", methods=["POST"])
def generate_report():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    # --- This part is unchanged ---
    selected_skills = request.form.getlist("skills")
    if not selected_skills:
        flash("Please select at least one skill.", "warning")
        return redirect(url_for('show_assessment_results'))

    student_data = {}
    # --- "testdrive" logic is unchanged ---
    if session.get('student_id') == 0:
        scores = session.get('test_user_scores', {})
        student_data = {
            'enrollment_no': 'testdrive', 'aq_score': scores.get('total_aq_score'),
            'control_score': scores.get('control_score'), 'ownership_score': scores.get('ownership_score'),
            'reach_score': scores.get('reach_score'), 'endurance_score': scores.get('endurance_score'),
            'attitude_score': scores.get('attitude_score')
        }
    else:
        # --- NEW SUPABASE CODE (SELECT) ---
        # Replaces get_db_connection, conn.execute, fetchone, and conn.close
        response = supabase.table('students').select(
            'enrollment_no, aq_score, control_score, ownership_score, reach_score, endurance_score, attitude_score'
        ).eq('id', session['student_id']).limit(1).execute()
        
        if response.data:
            student_data = response.data[0] # This is the new "dict(student)"
        # --- END OF NEW CODE ---

    if not student_data:
        flash("Could not retrieve student data.", "danger")
        return redirect(url_for('student_dashboard'))
    
    # --- This report generation logic is unchanged ---
    trait_scores = {
        "C": student_data['control_score'], "O": student_data['ownership_score'],
        "R": student_data['reach_score'], "E": student_data['endurance_score'],
        "A": student_data['attitude_score']
    }
    top_traits = [trait for trait, score in sorted(trait_scores.items(), key=lambda item: item[1], reverse=True)[:2]]

    final_recommendations = guidance_engine.generate_recommendations(
        enrollment=student_data['enrollment_no'], aq_score=student_data['aq_score'],
        skills=selected_skills, traits=top_traits
    )
    report_data = {"suggestions": [{"career": career, "reason": "This path aligns well with your calculated strengths and selected skills."} for career in final_recommendations]}
    
    # --- "testdrive" logic is unchanged ---
    if session.get('student_id') == 0:
        session['test_user_report_data'] = report_data
        session['test_user_skills'] = selected_skills
    else:
        # --- NEW SUPABASE CODE (UPDATE) ---
        # Replaces get_db_connection, conn.execute, conn.commit, and conn.close
        career_suggestion_json = json.dumps(report_data)
        
        response = supabase.table('students').update({
            "skills": ", ".join(selected_skills),
            "career_suggestion": career_suggestion_json
        }).eq('id', session['student_id']).execute()
        # --- END OF NEW CODE ---
    
    return redirect(url_for('student_report'))
# NEW, SECURE VERSION of student_report
# --- THIS IS THE NEW, SECURE VERSION of student_report ---
# --- THIS IS THE FINAL, MIGRATED VERSION ---
@app.route("/student/report")
@app.route("/student/report/<int:student_id>")
def student_report(student_id=None):
    # conn = get_db_connection() <-- REMOVED
    student_record = None
    # This new variable will track who is viewing the page
    viewer_is_teacher = False
    student = None # A helper variable to store the query result

    # Scenario 1: A teacher is viewing a student's report
    if 'teacher_id' in session and student_id is not None:
        viewer_is_teacher = True # We set this to True for the teacher
        
        # --- NEW SUPABASE CODE ---
        response = supabase.table('students').select('*').eq('id', student_id).limit(1).execute()
        if response.data:
            student = response.data[0] # This is the new "fetchone()"
        # --- END OF NEW CODE ---
        
        # Security Check: Ensure the student belongs to this teacher
        if student and student['teacher_id'] == session['teacher_id']:
            student_record = student # It's already a dict
        else:
            flash("Permission Denied: You can only view reports for students assigned to you.", "danger")
            # conn.close() <-- REMOVED
            return redirect(url_for('teacher_students'))

    # Scenario 2: A student is viewing their own report
    elif 'student_id' in session:
        student_id_from_session = session['student_id']
        
        # --- NEW SUPABASE CODE ---
        response = supabase.table('students').select('*').eq('id', student_id_from_session).limit(1).execute()
        if response.data:
            student = response.data[0] # This is the new "fetchone()"
        # --- END OF NEW CODE ---

        if student:
            student_record = student # It's already a dict
    
    # If no one valid is logged in, redirect them
    else:
        # conn.close() <-- REMOVED
        return redirect(url_for('student_login'))

    # Check if the report data exists before proceeding
    if not student_record or not student_record.get('aq_score'):
        flash("Report data not found. The student may need to complete the assessment first.", "warning")
        # conn.close() <-- REMOVED
        # Redirect to the correct dashboard based on who is logged in
        return redirect(url_for('teacher_students') if viewer_is_teacher else url_for('student_dashboard'))

    # --- The rest of your report generation logic is unchanged ---
    # ... (all the logic for suggestions, aq_category, trait_scores, etc. stays exactly the same) ...
    suggestions = []
    if student_record.get('career_suggestion'):
        # Add a check for empty string, just in case
        if student_record['career_suggestion']: 
            try:
                suggestions = json.loads(student_record['career_suggestion']).get('suggestions', [])
            except json.JSONDecodeError:
                suggestions = [] # Handle case where JSON is invalid
    
    aq_score = student_record['aq_score']
    if aq_score >= 180:
        aq_category = {"name": "Climber", "description": "You excel at navigating challenges and consistently seek growth. You are highly resilient and resourceful."}
    elif aq_score >= 160:
        aq_category = {"name": "Moderate Climber", "description": "You are resilient and consistently work to overcome challenges, showing a strong capacity for growth and adaptation."}
    elif aq_score >= 140:
        aq_category = {"name": "Camper", "description": "You are steady and reliable, but may sometimes avoid difficult challenges to stay in a comfortable zone."}
    elif aq_score >= 120:
        aq_category = {"name": "Moderate Camper", "description": "You handle familiar situations well but tend to avoid new or significant challenges. There's a great opportunity to step outside your comfort zone."}
    else:
        aq_category = {"name": "Quitter", "description": "You may feel overwhelmed by adversity and have an opportunity to develop stronger resilience strategies."}

    trait_scores = {
        "Control": student_record.get('control_score', 0), # Use .get() for safety
        "Ownership": student_record.get('ownership_score', 0),
        "Reach": student_record.get('reach_score', 0), 
        "Endurance": student_record.get('endurance_score', 0),
        "Attitude": student_record.get('attitude_score', 0)
    }
    top_traits_list = sorted(trait_scores.items(), key=lambda item: item[1], reverse=True)[:2]
    
    bloom_level_map = {
        "Control": "L1:Remembering, L3: Applying, L4: Analyzing", "Ownership": "L2: Understanding,L3: Applying, L4: Analyzing",
        "Reach": "L5: Evaluating", "Endurance": "L5: Evaluating", "Attitude": "L4: Analyzing, L6: Creating"
    }
    bloom_skill_map = {
        "L1": ["Remembrance"],
        "L2": ["Inference"],
        "L3": ["Solution-finding"],
        "L4": ["Reasoning"],
        "L5": ["Judgment"],
        "L6": ["Abstract resoning"]  # (I kept your spelling)
    }

    trait_skills_map = {}
    for trait, levels_str in bloom_level_map.items():
        level_codes = re.findall(r'L\d', levels_str)
        collected_skills = []
        for code in level_codes:
            collected_skills.extend(bloom_skill_map.get(code, []))
    trait_skills_map[trait] = list(dict.fromkeys(collected_skills))
    overall_top_skills = []
    seen_skills = set()
    for trait_name, trait_score in top_traits_list:
            skills = trait_skills_map.get(trait_name, [])
    for skill in skills:
        if skill not in seen_skills:
            overall_top_skills.append(skill)
            seen_skills.add(skill)
    # conn.close() <-- REMOVED
    
    # The final render_template call now includes the new variable
    return render_template(
        'student_report.html',
        student=student_record, aq_category=aq_category,
        trait_scores_json=json.dumps(trait_scores), top_traits=top_traits_list,
        suggestions=suggestions, bloom_map=bloom_level_map, trait_skills_map=trait_skills_map,
        viewer_is_teacher=viewer_is_teacher  # Pass the new variable to the HTML
    )

@app.route("/student/logout")
def student_logout():
    session.clear()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('student_login'))




"""
# Renamed the old /teachers to avoid conflict with login
@app.route("/teachers/info")
def teachers_info():
    return "<h1>Teacher info coming soon</h1>"
"""

if __name__ == "__main__":
    
    app.run(debug=True)

# This is a flask webapp

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'arsco_2030'  # Change this!
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


class TranslationSystem:
    def __init__(self):
        self.EXCEL_AUTH_FILE = "input_data.xlsx"
        self.events_df = pd.DataFrame()
        self.chapters_df = pd.DataFrame()
        self.staff_df = pd.DataFrame()
        self.follow_up_df = pd.DataFrame()
        self._load_data_silent()

    def _load_data_silent(self):
        """Load data without Flask context"""
        try:
            excel_data = pd.ExcelFile(self.EXCEL_AUTH_FILE)
            self.chapters_df = excel_data.parse('chapters')
            self.events_df = excel_data.parse('event')
            self.staff_df = excel_data.parse('staff')
            self.follow_up_df = excel_data.parse('follow_up')

            # Ensure email column exists
            if 'email' not in self.staff_df.columns:
                self.staff_df['email'] = ''  # Add empty email column

            print("[System] Data loaded successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Data loading failed: {e}")
            return False

    # ... [Keep all your existing methods unchanged] ...

    def is_user_in_chapter_staff(self, user_id, chapter_id):
        """Check if user is authorized for the given chapter"""
        try:
            staff = self.chapters_df.loc[self.chapters_df['chapter_id'] == chapter_id,
                                      ['manager', 'translator', 'checker_la', 'checker_sc']]
            if staff.empty:
                return False
            return user_id in staff.iloc[0].tolist()
        except Exception as e:
            print(f"[WARNING] Error checking user authorization: {e}")
            return False

    def add_event(self, user_id, chapter_id, chapter_version, action, message, url, document_path):
        """Add a new event to the events DataFrame"""
        try:
            event_id = self.events_df['event_id'].max() + 1 if not self.events_df.empty else 1
            event_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            new_event = pd.DataFrame({
                'event_id': [event_id],
                'event_date': [event_date],
                'event_creator': [user_id],
                'chapter_id': [chapter_id],
                'chapter_version': [chapter_version],
                'action': [action],
                'message': [message],
                'document_path': [document_path],
                'url': [url]
            })

            self.events_df = pd.concat([self.events_df, new_event], ignore_index=True)
            return True
        except Exception as e:
            print(f"[ERROR] Adding event: {e}")
            return False

    def add_follow_up(self, chapter_id, action_id):
        """Update follow-up dates based on action"""
        try:
            event_date = datetime.now().strftime('%Y-%m-%d')
            action_id = str(action_id)

            column_map = {
                "1": "translate_ass",
                "2": "check_lan_ass",
                "3": "check_sc_ass",
                "4": "translate_sub",
                "5": "check_lan_sub",
                "6": "check_sc_sub"
            }

            if action_id in column_map:
                column = column_map[action_id]
                self.follow_up_df.loc[self.follow_up_df["chapter_id"] == chapter_id, column] = event_date
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Updating follow-up: {e}")
            return False

    def save_data(self):
        """Save all DataFrames back to Excel file"""
        try:
            with pd.ExcelWriter(self.EXCEL_AUTH_FILE, engine='openpyxl') as writer:
                self.events_df.to_excel(writer, sheet_name='event', index=False)
                self.follow_up_df.to_excel(writer, sheet_name='follow_up', index=False)
                self.chapters_df.to_excel(writer, sheet_name='chapters', index=False)
                self.staff_df.to_excel(writer, sheet_name='staff', index=False)
            print("[System] Data saved successfully to", self.EXCEL_AUTH_FILE)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save data: {e}")
            return False

# Initialize system
try:
    translation_system = TranslationSystem()
except Exception as e:
    print(f"[CRITICAL] System initialization failed: {e}")
    sys.exit(1)


# --- Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        if not email:
            flash('Email is required', 'danger')
        elif email in translation_system.staff_df['email'].values:
            session['user_email'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Access denied. Use a registered work email.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_email', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


# --- Protected Routes ---
@app.route('/')
@login_required
def index():
    return render_template('index.html', user_email=session.get('user_email'))


@app.route('/submit_event', methods=['GET', 'POST'])
@login_required
def submit_event():
    if request.method == 'POST':
        try:
            # Get form data
            user_id = int(request.form['user_id'])
            chapter_id = request.form['chapter_id']
            chapter_version = int(request.form['chapter_version'])
            action = request.form['action']
            action_id = action[0]
            message = request.form['message']
            upload_file = 'upload_document' in request.form

            # Validate
            if not translation_system.is_user_in_chapter_staff(user_id, chapter_id):
                flash("You are not authorized for this chapter.", "error")
                return redirect(request.url)

            # Handle file upload
            document_path = None
            if upload_file and 'document' in request.files:
                file = request.files['document']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    l_name = translation_system.staff_df.loc[
                        translation_system.staff_df['staff_id'] == user_id, 'l_name'].values[0]
                    file_ext = os.path.splitext(filename)[1]
                    new_file_name = (
                        f"Ch{chapter_id}_version{chapter_version}_{action}_{l_name}_"
                        f"{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
                    )
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_file_name)
                    file.save(file_path)
                    document_path = file_path

            # Add records
            url = "http://example.com"  # Placeholder
            if (translation_system.add_event(user_id, chapter_id, chapter_version,
                                           action, message, url, document_path) and
                    translation_system.add_follow_up(chapter_id, action_id)):
                flash("Event submitted successfully!", "success")
                return redirect(url_for('index'))
            else:
                flash("Failed to save event data.", "error")

        except ValueError:
            flash("Invalid input. Please check your data.", "error")
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", "error")

    actions = [
        "1:Assign_translator", "2:Assign_checker_language", "3:Assign_checker_scientific",
        "4:Translator_sub", "5:Checker_language_sub", "6:Checker_scientific_sub", "7:Message"
    ]
    return render_template('submit_event.html', actions=actions)


@app.route('/view_events')
@login_required
def view_events():
    # Get filter parameters from request
    creator_id = request.args.get('creator_id', '')
    chapter_id = request.args.get('chapter_id', '')
    period = request.args.get('period', 'all')

    # Start with a copy of the original DataFrame
    filtered = translation_system.events_df.copy()

    try:
        # Apply filters
        if creator_id:
            filtered = filtered[filtered['event_creator'] == int(creator_id)]

        if chapter_id:
            filtered = filtered[filtered['chapter_id'] == chapter_id]

        if period != "all":
            today = datetime.now().date()
            if period == "today":
                filtered = filtered[pd.to_datetime(filtered['event_date']).dt.date == today]
            elif period == "last week":
                last_week = today - timedelta(days=7)
                filtered = filtered[pd.to_datetime(filtered['event_date']).dt.date >= last_week]
            elif period == "last month":
                last_month = today - timedelta(days=30)
                filtered = filtered[pd.to_datetime(filtered['event_date']).dt.date >= last_month]

        # Convert to list of dicts and handle document_path
        events_list = []
        for _, row in filtered.iterrows():
            event = row.to_dict()
            event['document_path'] = str(event.get('document_path', ''))
            events_list.append(event)

        return render_template('view_events.html',
                               events=events_list,
                               creator_id=creator_id,
                               chapter_id=chapter_id,
                               period=period)

    except Exception as e:
        print(f"Error filtering events: {e}")
        flash("Error loading events. Please try again.", "error")
        return redirect(url_for('index'))

@app.route('/save_data')
@login_required
def save_data():
    if translation_system.save_data():
        flash("Data saved successfully!", "success")
    else:
        flash("Failed to save data!", "error")
    return redirect(url_for('index'))

# --- File Handling ---
@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
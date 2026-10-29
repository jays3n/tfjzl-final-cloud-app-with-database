# IBM Django Online Course Final Project

Django online-course application with the exam assessment tasks completed: the Question, Choice, and Submission models; Django admin registration and inline classes; Bootstrap course details with lessons; and submit/result views plus routes.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations onlinecourse
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/admin/`. Create a Course, related Lesson(s), Question(s) for the course, and Choice(s) for each question. Mark correct choices. Sign up/login as a learner, enroll in a course, and submit its mock exam.

**Important:** This workspace is a locally prepared project. It must be pushed to the public GitHub repository named `jays3n/tfjzl-final-cloud-app-with-database` before using its GitHub file links in the Coursera grader.

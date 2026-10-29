import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from .models import Choice, Course, Enrollment, Question, Submission

logger = logging.getLogger(__name__)


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    username = request.POST.get('username', '').strip()
    password = request.POST.get('psw', '')
    first_name = request.POST.get('firstname', '')
    last_name = request.POST.get('lastname', '')
    if not username or not password:
        context['message'] = 'Username and password are required.'
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    if User.objects.filter(username=username).exists():
        context['message'] = 'User already exists.'
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password)
    login(request, user)
    return redirect('onlinecourse:index')


def login_request(request):
    context = {}
    if request.method == 'POST':
        user = authenticate(username=request.POST.get('username'), password=request.POST.get('psw'))
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        context['message'] = 'Invalid username or password.'
    return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    return bool(user.is_authenticated and Enrollment.objects.filter(user=user, course=course).exists())


class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        courses = Course.objects.order_by('-total_enrollment')[:10]
        user = self.request.user
        for course in courses:
            course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_details_bootstrap.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_enrolled'] = check_if_enrolled(self.request.user, self.object)
        return context


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if not request.user.is_authenticated:
        return redirect('onlinecourse:login')
    enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course, defaults={'mode': 'honor'})
    if created:
        course.total_enrollment += 1
        course.save(update_fields=['total_enrollment'])
    return HttpResponseRedirect(reverse('onlinecourse:course_details', args=(course.id,)))


def extract_answers(request):
    selected = []
    for key, value in request.POST.items():
        if key.startswith('choice'):
            try:
                selected.append(int(value))
            except (TypeError, ValueError):
                continue
    return selected


def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method != 'POST':
        return redirect('onlinecourse:course_details', pk=course.id)
    if not request.user.is_authenticated:
        return redirect('onlinecourse:login')
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)
    selected_ids = extract_answers(request)
    valid_choices = Choice.objects.filter(id__in=selected_ids, question__course=course)
    submission.choices.set(valid_choices)
    return redirect('onlinecourse:show_exam_result', course_id=course.id, submission_id=submission.id)


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id, enrollment__course=course)
    if not request.user.is_staff and submission.enrollment.user_id != request.user.id:
        return redirect('onlinecourse:login')

    questions = Question.objects.filter(course=course).prefetch_related('choice_set')
    selected_ids = list(submission.choices.values_list('id', flat=True))
    possible = sum(max(question.grade, 0) for question in questions)
    score = 0
    results = []
    for question in questions:
        choices = list(question.choice_set.all())
        selected_for_question = [c for c in choices if c.id in selected_ids]
        correct_choices = [c for c in choices if c.is_correct]
        correct = bool(correct_choices) and {c.id for c in selected_for_question} == {c.id for c in correct_choices}
        if correct:
            score += max(question.grade, 0)
        results.append({
            'question': question,
            'choices': choices,
            'selected_ids': [c.id for c in selected_for_question],
            'correct_ids': [c.id for c in correct_choices],
            'is_correct': correct,
        })
    grade = round(score * 100 / possible) if possible else 0
    context = {
        'course': course,
        'submission': submission,
        'results': results,
        'score': score,
        'possible': possible,
        'selected_ids': selected_ids,
        'choices': submission.choices.all(),
        'grade': grade,
        'percentage': grade,
        'passed': grade >= 80,
    }
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)

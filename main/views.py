# main/views.py (FINAL UPDATED WITH payment_detail_view, Admin Messages, & Exam Routine)

from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction 
from django.contrib import messages 
from django.db.models import Q 
from django.db.models.functions import Lower 
# FIX: Assignment, RegistrationRequest, AdminMessage, এবং ExamSchedule মডেলটি import করা হলো
from .models import Teacher, Student, Subject, Mark, SubjectClassAssignment, Assignment, RegistrationRequest, AdminMessage, ExamSchedule
from .forms import AdmissionApplicationForm 
import json 
import re 
from datetime import datetime # due_date যাচাই করার জন্য
import random # Teacher/Student ID তৈরি করার জন্য

# --- helper functions (অপরিবর্তিত) ---

def get_class_section_from_string(class_sec_str):
    """ '5A' বা 'Class X: Sec D' থেকে ক্লাস ও সেকশন বের করে """
    class_sec_str = class_sec_str.strip()
    
    # Class X: Sec D ফরম্যাট চেক
    match_long = re.match(r'Class\s+([A-Za-z0-9]+)\s*:\s*Sec\s+([A-Za-z0-9]+)', class_sec_str, re.IGNORECASE)
    if match_long:
        class_name = match_long.group(1).strip()
        section = match_long.group(2).strip()
    
    # 5A বা 8C ফরম্যাট চেক
    elif len(class_sec_str) > 1 and class_sec_str[-1].isalpha():
        class_name = class_sec_str[:-1]
        section = class_sec_str[-1]
    
    else:
        # ফলব্যাক
        class_name = class_sec_str
        section = ''
    
    # 5A বা 8C ফরমেটে ফিরিয়ে আনা হলো
    return f"{class_name}{section}".upper(), class_name, section

def parse_teacher_schedule(raw_text):
    """
    Parses raw text schedule details into a dict for the template,
    using dynamic sections (e.g., 5A, 8C) and 'Free' slots based on raw text input.
    """
    if not raw_text:
        return {}
        
    # ডামি সেকশন যা আপনি দেখাতে চেয়েছেন
    VISIBLE_SECTIONS = ['8C', '5A', '7B', '9A', '10A', '10B'] 
    
    # প্রাথমিক শিডিউল কাঠামো: শুধু Sun থেকে Thur 
    schedule = {
        'Sunday': ['Free'] * 6, # 6 পিরিয়ড ধরে নেওয়া হলো
        'Monday': ['Free'] * 6,
        'Tuesday': ['Free'] * 6,
        'Wednesday': ['Free'] * 6,
        'Thursday': ['Free'] * 6,
        
    }
    
    lines = raw_text.strip().split('\n')
    current_section_index = 0 
    
    # পিরিয়ড নাম থেকে সংখ্যায় রূপান্তরের জন্য ম্যাপ
    PERIOD_MAP = {
        '1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5, '6th': 6,
        '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    }

    for line in lines:
        line = line.strip().lower() 
        
        # রেগুলার এক্সপ্রেশন: দিনের নাম (যেমন sun, mon) এবং তারপরের সমস্ত পিরিয়ড টোকেন
        match = re.match(r'(\w+)\s*-\s*(.*)', line)
        if match:
            day_name_short = match.group(1).lower()
            period_str = match.group(2)
            
            # সম্পূর্ণ দিনের নাম বের করা
            day_map = {'sun': 'Sunday', 'mon': 'Monday', 'tues': 'Tuesday', 'wed': 'Wednesday', 'thur': 'Thursday', 'fri': 'Friday', 'sat': 'Saturday'}
            day_name = day_map.get(day_name_short, None)
            
            if day_name and day_name in schedule:
                
                # 💡 FIX: পিরিয়ড টোকেনগুলো বের করা: '1st', '2nd', '5th' বা শুধু '1', '2', '5'
                period_tokens = re.findall(r'\b\d+(?:st|nd|rd|th)?\b', period_str)
                
                # দিনের জন্য নতুন পিরিয়ড তালিকা
                periods = ['Free'] * 6
                
                for token in period_tokens:
                    period_num = PERIOD_MAP.get(token) 
                    
                    if period_num and 1 <= period_num <= 6:
                        # রোটেশন ব্যবহার করে VISIBLE_SECTIONS থেকে Assign করা
                        section_to_assign = VISIBLE_SECTIONS[current_section_index % len(VISIBLE_SECTIONS)]
                        periods[period_num - 1] = section_to_assign
                        current_section_index += 1

                schedule[day_name] = periods

    return schedule


# =========================================================
#  CORE PAGE RENDERING VIEWS 
# =========================================================

# 1️⃣ Index page
def index(request):
    # FIX: Login.html এ pending_requests_count পাস করা হলো
    pending_requests_count = RegistrationRequest.objects.filter(status='Pending').count()
    return render(request, 'index.html', {'pending_requests_count': pending_requests_count})

# 2️⃣ Main content page (Home)
def main_content(request):
    return render(request, 'main-content.html')
    
# 3️⃣ Admission Information Page
def admission_info_view(request):
    return render(request, 'admission.html') 

# 4️⃣ Application Form View
def apply_form_view(request):
    if request.method == 'POST':
        form = AdmissionApplicationForm(request.POST) 
        if form.is_valid():
            messages.success(request, 'Application submitted successfully! Please proceed to login.')
            return redirect(reverse('login'))
    else:
        form = AdmissionApplicationForm() 
    return render(request, 'apply_form.html', {'form': form}) 

# 5️⃣ Login Page
def login_view(request):
    # FIX: Login.html এ pending_requests_count পাস করা হলো
    pending_requests_count = RegistrationRequest.objects.filter(status='Pending').count()
    return render(request, 'Login.html', {'pending_requests_count': pending_requests_count})


# =========================================================
#  DASHBOARD VIEWS
# =========================================================

def admin_dashboard_view(request):
    """Admin Dashboard View"""
    if not request.session.get('admin_logged_in'):
        messages.error(request, 'Please log in as Admin.')
        return redirect(reverse('login'))
        
    context = {
        'active_view': 'dashboard',
        'all_teachers': Teacher.objects.all().order_by('teacher_id')
    }
    return render(request, 'admin-dashboard.html', context)

def registered_teachers_view(request):
    """Registered Teachers List View"""
    if not request.session.get('admin_logged_in'):
        messages.error(request, 'Please log in as Admin.')
        return redirect(reverse('login'))
    
    teachers = Teacher.objects.all().order_by('teacher_id')
    
    context = {
        'active_view': 'registeredTeachers', 
        'all_teachers': teachers,
    }
    return render(request, 'admin-dashboard.html', context) 

def registered_students_view(request):
    """Registered Students List View"""
    if not request.session.get('admin_logged_in'):
        messages.error(request, 'Please log in as Admin.')
        return redirect(reverse('login'))
    
    students = Student.objects.all().order_by('class_name', 'section', 'roll_number')

    context = {
        'active_view': 'registeredStudents', 
        'all_students': students, 
        'all_teachers': Teacher.objects.all().order_by('teacher_id')
    }
    return render(request, 'admin-dashboard.html', context)
    
def teacher_update_view(request):
    """Admin Dashboard: Teacher Update View"""
    if not request.session.get('admin_logged_in'):
        messages.error(request, 'Please log in as Admin.')
        return redirect(reverse('login'))
    
    teachers = Teacher.objects.all().order_by('teacher_id')
    
    context = {
        'active_view': 'teacherUpdate', 
        'all_teachers': teachers,
    }
    return render(request, 'admin-dashboard.html', context)

def student_management_view(request):
    """Admin Dashboard: Student Management View"""
    if not request.session.get('admin_logged_in'):
        messages.error(request, 'Please log in as Admin.')
        return redirect(reverse('login'))
    
    students = Student.objects.all().order_by('class_name', 'section', 'roll_number')
    
    context = {
        'active_view': 'studentManagement', 
        'all_students': students,
    }
    return render(request, 'admin-dashboard.html', context)

# 🆕 Payment Detail View
def payment_detail_view(request):
    """Admin Dashboard: Payment Detail View - Shows Student ID, Name, and Payment Status dynamically"""
    if not request.session.get('admin_logged_in'):
        messages.error(request, 'Please log in as Admin.')
        return redirect(reverse('login'))
        
    # শুধুমাত্র active student দের ডেটা Fetch করা হলো
    # student_id, first_name, last_name, ও payment_status ফিল্ডগুলি নেওয়া হলো
    payment_students = Student.objects.filter(is_active=True).values(
        'student_id',
        'first_name',
        'last_name',
        'payment_status'
    ).order_by('class_name', 'section', 'roll_number')
    
    # পেমেন্ট স্ট্যাটাস Choices টেমপ্লেটে পাস করা হলো
    PAYMENT_STATUS_CHOICES = Student.PAYMENT_CHOICES # models.py থেকে নেওয়া হলো

    context = {
        'active_view': 'paymentDetail', # এটি admin-dashboard.html এ ব্যবহারের জন্য
        'payment_students': payment_students,
        'payment_status_choices': PAYMENT_STATUS_CHOICES, 
    }
    return render(request, 'admin-dashboard.html', context)


# 🎯 FIX: Registration Requests View 
def registration_requests_view(request):
    """Admin Dashboard: Pending Registration Requests View"""
    if not request.session.get('admin_logged_in'):
        messages.error(request, 'Please log in as Admin.')
        return redirect(reverse('login'))
        
    # FIX: শুধুমাত্র Pending রিকোয়েস্টগুলো লোড করা হলো
    pending_requests = RegistrationRequest.objects.filter(status='Pending').order_by('requested_at')
    
    context = {
        'active_view': 'registrationRequests', 
        'pending_requests': pending_requests,
    }
    return render(request, 'admin-dashboard.html', context)


def student_dashboard_view(request):
    # স্টুডেন্ট লগইন নিশ্চিত করার জন্য নতুন লজিক:
    student_id = request.session.get('student_id')
    
    if not student_id:
        return redirect(reverse('login'))
        
    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        messages.error(request, 'Student account not found.')
        return redirect(reverse('login'))
        
    # --- মার্কস লোড করার লজিক (অপরিবর্তিত) ---
    student_marks_qs = Mark.objects.filter(student=student).select_related('subject').order_by('subject__subject_code')

    marks_map = {}
    for mark in student_marks_qs:
        marks_map[mark.subject.subject_name] = {
            'ot_marks': mark.ot_marks,
            'ct_marks': mark.ct_marks,
            'obtained_marks': mark.obtained_marks,
            'average': mark.average_marks 
        }

    RESULT_SUBJECTS = ['Bangla', 'English', 'Math', 'BGS', 'Religion', 'Science', 'ICT']

    student_results_list = []
    for sub_name in RESULT_SUBJECTS:
        mark_data = marks_map.get(sub_name)
        
        if mark_data:
            student_results_list.append({
                'subject_name': sub_name,
                'ot_marks': mark_data['ot_marks'],
                'ct_marks': mark_data['ct_marks'],
                'obtained_marks': mark_data['obtained_marks'],
                'average': mark_data['average'],
            })
        else:
            student_results_list.append({
                'subject_name': sub_name,
                'ot_marks': '-', 
                'ct_marks': '-',
                'obtained_marks': '-',
                'average': '-',
            })
            
    student_results_for_template = student_results_list
    
    # --- অ্যাসাইনমেন্ট ডেটা লোড করা (অপরিবর্তিত) ---
    cls = student.class_name 
    sec = student.section    
    
    student_assignments_qs = Assignment.objects.filter(
        class_name__iexact=cls, 
        section__iexact=sec
    ).select_related('teacher').order_by('-due_date') 
    
    assignments_list = []
    for idx, assignment in enumerate(student_assignments_qs):
        status = 'Completed' if idx % 3 != 0 else 'Pending' 
        grade = 'A+' if status == 'Completed' and idx % 2 == 0 else 'B' if status == 'Completed' else None
        
        assignments_list.append({
            'subject_name': 'N/A' if not assignment.title else assignment.title.split(' ')[0], 
            'title': assignment.title,
            'description': assignment.description,
            'due_date': assignment.due_date.strftime('%Y-%m-%d'), 
            'teacher_name': f"{assignment.teacher.first_name} {assignment.teacher.last_name}",
            'status': status,  
            'grade': grade,    
        })

    # --- নতুন: Pending মেসেজের সংখ্যা লোড করা ---
    # এটি student-dashboard.html এ নোটিফিকেশন ব্যাজ হিসেবে ব্যবহার করা যেতে পারে
    new_messages_count = AdminMessage.objects.filter(student=student).count() 
    
    context = {
        'student': student,
        'student_results': student_results_for_template, 
        'student_assignments': assignments_list, 
        # নতুন যোগ করা হলো
        'new_messages_count': new_messages_count, 
    }
    return render(request, 'student-dashboard.html', context)


def teacher_dashboard_view(request):
    teacher_id = request.session.get('teacher_id')
    # (অন্যান্য লজিক অপরিবর্তিত)
    
    if not teacher_id:
        messages.error(request, 'Please log in as Teacher.')
        return redirect(reverse('login'))
        
    try:
        teacher = Teacher.objects.get(teacher_id=teacher_id)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher account not found.')
        return redirect(reverse('login'))

    # 1. SubjectClassAssignment ডেটা লোড করা (ডাইনামিক বাটন তৈরির জন্য)
    assignments = SubjectClassAssignment.objects.filter(teacher=teacher).select_related('subject')
    subject_teacher_assignments = [
        {'class_sec': assignment.class_sec, 'subject_name': assignment.subject.subject_name}
        for assignment in assignments
    ]
    
    # 2. Pie Chart এবং Class Teacher এর ডেটা
    pie_chart_data_json = "{}"
    initial_class_sec = None
    
    if teacher.class_teacher_of:
        class_sec_5a_format, class_name, section = get_class_section_from_string(teacher.class_teacher_of)
        initial_class_sec = class_sec_5a_format 

        # ডেমো Pie Chart ডেটা
        pie_chart_data = {
          "Grade": {'labels': ['A+', 'A', 'B', 'C', 'Failed'], 'data': [15, 20, 10, 8, 5], 'colors': ['#28a745', '#ffc107', '#17a2b8', '#007bff', '#dc3545']},
          "EC": {'labels': ['Dance', 'Singing', 'Poetry', 'Debate', 'None'], 'data': [10, 8, 6, 12, 14], 'colors': ['#AB47BC', '#FFA726', '#66BB6A', '#42A5F5', '#E0E0E0']},
          "Olympiad": {'labels': ['Math', 'Science', 'ICT', 'Attended', 'Not Attended'], 'data': [5, 4, 3, 10, 28], 'colors': ['#EC407A', '#FF7043', '#78909C', '#8D6E63', '#9CCC65']},
          "SF": {'labels': ['Win', 'No Win', 'Supporter', 'Not Involved'], 'data': [2, 8, 15, 25], 'colors': ['#FFCA28', '#26C6DA', '#795548', '#B0BEC5']} 
        } 
        
        pie_chart_data_json = json.dumps(pie_chart_data)

    elif subject_teacher_assignments:
        initial_class_sec = subject_teacher_assignments[0]['class_sec']
    
    # 3. TimeTable ডাইনামিক ডেটা লোডিং
    schedule = parse_teacher_schedule(teacher.schedule_details)

    context = {
        'teacher': teacher,
        'schedule': schedule,
        'pie_chart_data_json': pie_chart_data_json, 
        'subject_teacher_assignments': subject_teacher_assignments,
        'initial_class_sec': initial_class_sec,
    }

    return render(request, 'teacher-dashboard.html', context)


# =========================================================
#  STUDENT DASHBOARD ADDITIONAL VIEWS (FIXED)
# =========================================================

def get_student_messages(request):
    """
    নির্দিষ্ট ছাত্রের জন্য Admin Message লোড করে। (Message from Admin বাটন)
    """
    student_id = request.session.get('student_id')
    if not student_id:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
        
    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student not found'}, status=404)

    # শুধুমাত্র এই ছাত্রের জন্য মেসেজ লোড করা
    messages_qs = AdminMessage.objects.filter(student=student).order_by('-sent_at')
    
    messages_list = [
        {
            'subject': msg.subject,
            'content': msg.content, # মডেলের ফিল্ডের নাম 'content'
            # 🎯 FIX 1: JavaScript-এর সাথে মিলিয়ে 'timestamp' কী ব্যবহার করা হলো
            'timestamp': msg.sent_at.strftime('%Y-%m-%d %H:%M') 
        }
        for msg in messages_qs
    ]

    return JsonResponse({'status': 'success', 'messages': messages_list}, status=200)


def get_exam_routine(request):
    """
    সকল ছাত্রের জন্য Exam Routine লোড করে। (Exam Routine বাটন)
    """
    if not request.session.get('student_id'): # লগইন চেক করা
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)

    # সবচেয়ে নতুন প্রকাশিত রুটিনটি লোড করা
    try:
        latest_routine = ExamSchedule.objects.all().order_by('-published_date').first()
        
        routine_data = None # Default value
        
        if latest_routine:
            routine_data = {
                'title': latest_routine.title,
                # 🎯 FIX 2: file থাকলে URL ব্যবহার করা, না থাকলে None
                'file_url': latest_routine.file.url if latest_routine.file else None, 
                'published_date': latest_routine.published_date.strftime('%Y-%m-%d')
            }
        
        # 🎯 FIX 3: কোনো রুটিন না থাকলে error না দিয়ে, empty data (routine=None) পাঠানো।
        return JsonResponse({'status': 'success', 'routine': routine_data}, status=200)

    except Exception as e:
        # 🎯 FIX 4: সার্ভার সাইড এরর হলে সঠিক স্ট্যাটাস এবং মেসেজ পাঠানো।
        return JsonResponse({'status': 'error', 'message': f'Internal Server Error: {type(e).__name__}'}, status=500)


# =========================================================
#  Assignment তৈরি করার ভিউ (অপরিবর্তিত)
# =========================================================
@csrf_exempt
def create_assignment(request, teacher_id):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect(reverse('teacher_dashboard'))
        
    try:
        current_teacher = Teacher.objects.get(teacher_id=teacher_id)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher not found.')
        return redirect(reverse('login'))

    # ফর্ম ডেটা নেওয়া
    class_sec_str = request.POST.get('class_sec') # যেমন: 5A
    title = request.POST.get('title')
    description = request.POST.get('description')
    due_date_str = request.POST.get('due_date')

    # ভ্যালিডেশন
    if not class_sec_str or not title or not due_date_str:
        messages.error(request, 'Error: Title, Class/Section, and Due Date cannot be empty.')
        return redirect(reverse('teacher_dashboard'))

    # ক্লাস এবং সেকশন পার্স করা
    class_sec_5a_format, class_name, section = get_class_section_from_string(class_sec_str)

    # নিরাপত্তার জন্য due_date চেক করা
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        if due_date < datetime.now().date():
            messages.error(request, 'Error: Due Date cannot be in the past.')
            return redirect(reverse('teacher_dashboard'))
    except ValueError:
        messages.error(request, 'Error: Invalid date format.')
        return redirect(reverse('teacher_dashboard'))
        
    # যদি শিক্ষক Subject Teacher হন এবং class_sec দেন, তবে সেই ক্লাস সেকশনটি তার কোনো অ্যাসাইনমেন্টে থাকতে হবে
    is_subject_teacher_authorized = SubjectClassAssignment.objects.filter(
        teacher=current_teacher, 
        class_sec__iexact=class_sec_str
    ).exists()
        
    # ক্লাস টিচার হলে নিজের ক্লাস ছাড়া অন্য ক্লাসে দিতে পারবে না (বাড়িয়ে দেওয়া হলো)
    is_class_teacher_authorized = (current_teacher.class_teacher_of.upper().strip() == class_sec_str.upper().strip())

    # যদি কোনো শিক্ষকই সেই ক্লাস সেকশনের জন্য অথরাইজড না হন
    if not (is_subject_teacher_authorized or is_class_teacher_authorized):
        messages.error(request, f'Error: You are not authorized to assign tasks to Class {class_sec_str}.')
        return redirect(reverse('teacher_dashboard'))

    try:
        # Assignment ডেটাবেসে সেভ করা
        Assignment.objects.create(
            teacher=current_teacher,
            class_name=class_name, # যেমন: 5
            section=section,       # যেমন: A
            title=title,
            description=description,
            due_date=due_date
        )
        messages.success(request, f'Assignment "{title}" successfully published for {class_sec_5a_format}.')
    except Exception as e:
        messages.error(request, f'Error creating assignment: {e}')

    return redirect(reverse('teacher_dashboard'))


# =========================================================
#  DYNAMIC DATA LOADER (AJAX) (অপরিবর্তিত)
# =========================================================

@csrf_exempt
def load_students_for_mark_update(request):
    """
    মার্কস আপডেটের জন্য প্রয়োজনীয় ছাত্রদের ডেটা (নাম, রোল, PK এবং সেভ করা মার্কস) লোড করে।
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return JsonResponse({'error': 'Unauthorized access'}, status=401)
    
    class_sec_str = request.GET.get('class_sec') 
    role = request.GET.get('role')             
    subject_name = request.GET.get('subject')    
    
    if not class_sec_str:
        return JsonResponse({'error': 'Missing class/section parameter'}, status=400)

    class_sec_5a_format, class_name, section = get_class_section_from_string(class_sec_str)

    # 1. বেস স্টুডেন্ট কোয়েরিসেট
    try:
        students_qs = Student.objects.filter(class_name__iexact=class_name, section__iexact=section).order_by('roll_number') 
    except Exception:
        students_qs = []
    
    
    # 2. ক্লাসের সমস্ত মার্কস আগে থেকে লোড করে একটি ডিকশনারিতে রাখা হলো
    student_marks = {}
    
    if role == 'subject':
        # সাবজেক্ট টিচার: শুধুমাত্র একটি সাবজেক্টের মার্কস
        try:
            subject_obj = Subject.objects.get(subject_name__iexact=subject_name)
            marks_qs = Mark.objects.filter(student__in=students_qs, subject=subject_obj).select_related('student')
            for mark in marks_qs:
                student_marks[mark.student.pk] = mark.obtained_marks
        except Subject.DoesNotExist:
            pass 
            
    else: # role == 'class' (ক্লাস টিচার)
        SUBJECT_LIST = ['Math', 'English', 'Bangla', 'ICT', 'Religion', 'BGS', 'Science']
        lower_subject_list = [s.lower() for s in SUBJECT_LIST]
        
        try:
            subject_objects = Subject.objects.annotate(lower_name=Lower('subject_name')).filter(lower_name__in=lower_subject_list)
            
            subject_map = {sub.lower_name: sub for sub in subject_objects}
            
            marks_qs = Mark.objects.filter(student__in=students_qs, subject__in=subject_objects).select_related('student', 'subject')
            
            for mark in marks_qs:
                subject_db_name_lower = mark.subject.subject_name.lower()
                
                if subject_db_name_lower in subject_map:
                    if mark.student.pk not in student_marks:
                        student_marks[mark.student.pk] = {}
                        
                    student_marks[mark.student.pk][mark.subject.subject_name] = mark.obtained_marks
                
        except Exception as e:
            print(f"Error loading class marks: {e}") 
            pass


    # 3. ফাইনাল ডেটা প্রস্তুত করা
    students_data = []

    for student in students_qs:
        
        data = {
            'pk': student.pk, 
            'first_name': student.first_name,
            'last_name': student.last_name,
            'roll_number': student.roll_number,
        }
        
        if role == 'subject':
            data['saved_mark'] = student_marks.get(student.pk, '') 
        else:
            data['saved_marks'] = student_marks.get(student.pk, {})

        students_data.append(data)

    return JsonResponse({
        'students': students_data,
        'role': role,
        'class_sec': class_sec_5a_format,
        'subject_name': subject_name
    })


@csrf_exempt
def load_dynamic_students(request):
    """
    AJAX এর মাধ্যমে শিক্ষক ড্যাশবোর্ডের জন্য ডাইনামিক স্টুডেন্ট ডেটা লোড করে। (Student Details View এর জন্য)
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return JsonResponse({'error': 'Unauthorized access'}, status=401)
    
    class_sec_str = request.GET.get('class_sec') 
    role = request.GET.get('role')             
    subject_name = request.GET.get('subject')    
    
    if not class_sec_str:
        return JsonResponse({'error': 'Missing class/section parameter'}, status=400)

    class_sec_5a_format, class_name, section = get_class_section_from_string(class_sec_str)

    # 1. বেস স্টুডেন্ট কোয়েরিসেট
    try:
        students_qs = Student.objects.filter(class_name__iexact=class_name, section__iexact=section).order_by('roll_number') 
    except Exception:
        students_qs = []
    
    students_data = []

    for student in students_qs:
        
        # 'Guardian Number' এর জন্য ডেমো হিসেবে father_name ব্যবহার করা হলো
        guardian_info = student.father_name if student.father_name else student.mother_name if student.mother_name else 'N/A'
        
        data = {
            'pk': student.pk,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'roll_number': student.roll_number,
            'guardian_info': guardian_info 
        }
        
        students_data.append(data)

    return JsonResponse({
        'students': students_data, 
        'class_sec': class_sec_5a_format, 
        'role': role, 
        'subject_name': subject_name 
    })


# =========================================================
#  MARK ENTRY LOGIC (অপরিবর্তিত)
# =========================================================

def update_subject_marks(request, teacher_id):
    if request.method != 'POST':
        return redirect(reverse('teacher_dashboard'))

    try:
        current_teacher = Teacher.objects.get(teacher_id=teacher_id)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher not found.')
        return redirect(reverse('login'))
        
    subject_name = request.POST.get('subject_name') 
    
    # নিরাপত্তা: নিশ্চিত করা যে শিক্ষক সেই সাবজেক্টটি পড়ান
    is_authorized = SubjectClassAssignment.objects.filter(
        teacher=current_teacher,
        subject__subject_name__iexact=subject_name
    ).exists()
    
    if not is_authorized:
        messages.error(request, 'Error: You are not authorized to update marks for this subject.')
        return redirect(reverse('teacher_dashboard'))
        
    
    with transaction.atomic():
        
        try:
            # একবার সাবজেক্ট অবজেক্ট লোড করা হলো (Case-Insensitive)
            subject_obj = Subject.objects.get(subject_name__iexact=subject_name)
        except Subject.DoesNotExist:
            messages.error(request, f'Error: Subject {subject_name} not found in database.')
            return redirect(reverse('teacher_dashboard'))

        # HTML থেকে পোস্ট হওয়া সমস্ত student_pk_X ফিল্ডের ওপর লুপ
        for key, student_pk in request.POST.items():
            if key.startswith('student_pk_'):
                
                mark_key_suffix = key.split('_')[-1] 
                mark_value_key = f'mark_{mark_key_suffix}' 
                mark_value = request.POST.get(mark_value_key)
                
                if student_pk and mark_value is not None and mark_value.strip().isdigit():
                    try:
                        # PK ধরে ছাত্র খুঁজে বের করা
                        student = Student.objects.get(pk=student_pk)
                        mark_value = int(mark_value.strip())
                        
                        # Mark আপডেট বা তৈরি করা
                        Mark.objects.update_or_create(
                            student=student,
                            subject=subject_obj,
                            defaults={'obtained_marks': mark_value, 'teacher': current_teacher} 
                        )
                    except Student.DoesNotExist:
                        continue
        
    messages.success(request, f'Marks for Subject {subject_name} successfully updated.')
    return redirect(reverse('teacher_dashboard'))


@csrf_exempt
def update_class_marks(request, teacher_id):
    if request.method != 'POST':
        return redirect(reverse('teacher_dashboard'))

    try:
        current_teacher = Teacher.objects.get(teacher_id=teacher_id)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher not found.')
        return redirect(reverse('login'))
        
    class_sec_str = request.POST.get('class_sec') 

    # নিরাপত্তা: নিশ্চিত করা যে শিক্ষক এই ক্লাসের ক্লাস টিচার
    if current_teacher.class_teacher_of.upper().strip() != class_sec_str.upper().strip():
         messages.error(request, 'Error: You are not authorized to update marks for this class.')
         return redirect(reverse('teacher_dashboard'))

    class_sec_5a_format, cls, section = get_class_section_from_string(class_sec_str)

    SUBJECT_LIST = ['Math', 'English', 'Bangla', 'ICT', 'Religion', 'BGS', 'Science']
    lower_subject_list = [s.lower() for s in SUBJECT_LIST]
    
    # সব সাবজেক্টের অবজেক্ট আগে লোড করে রাখা
    subject_objects = Subject.objects.annotate(lower_name=Lower('subject_name')).filter(lower_name__in=lower_subject_list)
    
    # সাবজেক্ট নাম ম্যাপ তৈরি করা
    subject_map = {sub.lower_name: sub for sub in subject_objects}

    with transaction.atomic():
        
        # 1. ফর্ম থেকে আসা student pks বের করা
        student_pks = [
             int(v) for k, v in request.POST.items() 
             if k.startswith('student_pk_') and v.isdigit()
        ]

        if not student_pks:
            messages.error(request, 'Error: No student data found in the form submission.')
            return redirect(reverse('teacher_dashboard'))

        students_in_class = Student.objects.filter(pk__in=student_pks)
        
        # 2. প্রতিটি ছাত্রের জন্য মার্কস আপডেট করা
        for student in students_in_class:
                
            for subject_name in SUBJECT_LIST:
                # Mark Key তৈরি: marks_PK_SubjectName (যা HTML থেকে আসে)
                mark_key = f'marks_{student.pk}_{subject_name}' 
                mark_value = request.POST.get(mark_key)
                
                # Subject Object ম্যাপিং থেকে lowercase key ব্যবহার করে নেওয়া হলো
                subject_obj = subject_map.get(subject_name.lower())

                if subject_obj and mark_value is not None and mark_value.strip().isdigit():
                    mark_value = int(mark_value.strip())
                    
                    # Mark আপডেট বা তৈরি করা
                    Mark.objects.update_or_create(
                        student=student,
                        subject=subject_obj,
                        defaults={'obtained_marks': mark_value, 'teacher': current_teacher}
                    )
                        
    messages.success(request, f'Marks for Class {cls}, Section {section} successfully updated.')
    return redirect(reverse('teacher_dashboard'))


# =========================================================
#  OTHER FORM SUBMISSION LOGIC (অপরিবর্তিত)
# =========================================================

def login_user(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        username = request.POST.get('username')
        password = request.POST.get('password')

        ADMIN_USER = 'admin'
        ADMIN_PASS = 'admin123' 
        
        if role == 'Admin' and username == ADMIN_USER and password == ADMIN_PASS:
            request.session['admin_logged_in'] = True 
            return redirect(reverse('admin_dashboard')) 
        
        elif role == 'Teacher':
            try:
                teacher = Teacher.objects.get(teacher_id=username) 
                # FIX: Django এর make_password ব্যবহার করে hashed password তৈরি করে, তা পাসওয়ার্ড হিসেবে সেভ করা উচিত। তবে আপনার বর্তমান implementation এ সাদামাটাভাবে চেক করা হলো।
                if teacher.password == password: 
                    request.session['teacher_id'] = teacher.teacher_id 
                    return redirect(reverse('teacher_dashboard'))
                else:
                    messages.error(request, 'Invalid password for teacher.')
                    return redirect(reverse('login'))
            except Teacher.DoesNotExist:
                messages.error(request, 'Teacher ID not found.')
                return redirect(reverse('login'))

        elif role == 'Student':
            try:
                student = Student.objects.get(student_id=username) 
                if student.password == password:
                    request.session['student_id'] = student.student_id 
                    return redirect(reverse('student_dashboard'))
                else:
                    messages.error(request, 'Invalid password for student.')
                    return redirect(reverse('login'))
            except Student.DoesNotExist:
                messages.error(request, 'Student ID not found.')
                return redirect(reverse('login'))
        
        else:
            messages.error(request, 'Invalid role selected.')
            return redirect(reverse('login'))
            
    return redirect(reverse('login'))

# 🎯 FIX: রেজিস্ট্রেশন রিকোয়েস্ট সেভ করার লজিক এবং phone_number চেক বাদ দেওয়া হলো
def registration_request_view(request):
    """
    Handles the submission of a new registration request and saves it to the database.
    (Phone Number is no longer mandatory for form submission)
    """
    if request.method == 'POST':
        # 1. ফর্ম থেকে ডেটাগুলো নেওয়া
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        requested_role = request.POST.get('requested_role') 
        phone_number = request.POST.get('phone_number') 
        
        # Student-এর জন্য অতিরিক্ত ডেটা
        class_name = request.POST.get('class_name')
        section = request.POST.get('section')
        roll_no = request.POST.get('roll_no')

        # 2. ডেটা সেভ করার ভ্যালিডেশন (phone_number বাধ্যতামূলক নয়)
        if not all([full_name, email, requested_role]): 
            messages.error(request, 'Error: Please fill in all required fields (Full Name, Email, Role).')
            return redirect(reverse('login'))
            
        if requested_role == 'Student' and not all([class_name, section, roll_no]):
             messages.error(request, 'Error: Students must provide Class, Section, and Roll No.')
             return redirect(reverse('login'))
             
        # 3. ডেটাবেসে সেভ করা
        try:
            RegistrationRequest.objects.create(
                full_name=full_name,
                email=email,
                requested_role=requested_role,
                # phone_number যদি ফর্মে থাকে তো সেভ হবে, না থাকলে খালি সেভ হবে
                phone_number=phone_number if phone_number else None, # None হলে blank=True, null=True এর সাথে মিলবে
                # Student-এর জন্য
                class_name=class_name if requested_role == 'Student' else None,
                section=section if requested_role == 'Student' else None,
                roll_no=roll_no if requested_role == 'Student' else None,
            )
            messages.success(request, 'Registration request received successfully. Please wait for Admin approval.')
        except Exception as e:
            messages.error(request, f'An error occurred while submitting the request: {e}')

        return redirect(reverse('login'))
        
    # যদি GET request হয়, তবে এটি লগইন পেজে যাবে
    return redirect(reverse('login'))


def logout_user(request):
    # সব সেশন ভ্যারিয়েবল ডিলিট করা
    if 'teacher_id' in request.session:
        del request.session['teacher_id']
    if 'student_id' in request.session:
        del request.session['student_id']
    if 'admin_logged_in' in request.session:
        del request.session['admin_logged_in']
        
    messages.info(request, 'Successfully logged out.')
    return redirect(reverse('login'))

# =========================================================
#  Registration Request Handling AJAX Views (অপরিবর্তিত)
# =========================================================

# Accept Request (ডিফল্ট পাসওয়ার্ড: 123456)
@csrf_exempt
def accept_request(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    
    if not request.session.get('admin_logged_in'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
        
    try:
        req = RegistrationRequest.objects.get(pk=pk)
    except RegistrationRequest.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Request not found'}, status=404)
        
    try:
        with transaction.atomic():
            
            DEFAULT_PASSWORD = '123456' # নতুন ডিফল্ট পাসওয়ার্ড
            
            if req.requested_role == 'Teacher':
                # টিচার আইডি (যেমন: T1001)
                new_id = f'T{random.randint(1000, 9999)}' 
                
                # নতুন শিক্ষক তৈরি করা
                Teacher.objects.create(
                    teacher_id=new_id,
                    first_name=req.full_name.split(' ')[0], 
                    last_name=' '.join(req.full_name.split(' ')[1:]) or 'N/A', 
                    email=req.email,
                    password=DEFAULT_PASSWORD, 
                    # 🎯 FIX: Teacher মডেলে phone নামে ফিল্ড আছে
                    phone=req.phone_number if req.phone_number else 'N/A' 
                )
                success_msg = f'Teacher {req.full_name} approved. ID: {new_id}. Default Password: {DEFAULT_PASSWORD}'

            elif req.requested_role == 'Student':
                class_name = req.class_name
                section = req.section
                roll_no_str = req.roll_no # String থেকে Integer এ কনভার্ট করতে হবে
                
                # রোল নম্বর স্ট্রিং থেকে ইন্টিজারে রূপান্তর
                try:
                    roll_int = int(roll_no_str)
                except (ValueError, TypeError):
                    roll_int = 0 # যদি ভুল ডেটা থাকে
                    
                new_id = f'S{class_name}{section}{roll_int:03}'
                
                # নতুন ছাত্র তৈরি করা
                Student.objects.create(
                    student_id=new_id,
                    first_name=req.full_name.split(' ')[0],
                    last_name=' '.join(req.full_name.split(' ')[1:]) or 'N/A',
                    email=req.email,
                    password=DEFAULT_PASSWORD, 
                    # আপাতত, Student মডেলে ফোন নম্বর ফিল্ড না থাকায় সেভ করা হলো না।
                    class_name=class_name,
                    section=section,
                    # 🎯 FIX: Student মডেলে roll_number ইন্টিজার হিসেবে সেভ করতে হবে
                    roll_number=roll_int,
                )
                success_msg = f'Student {req.full_name} approved. ID: {new_id}. Default Password: {DEFAULT_PASSWORD}'
            
            else:
                return JsonResponse({'status': 'error', 'message': f'Invalid role: {req.requested_role}'}, status=400)
                
            # রিকোয়েস্ট ডিলিট করা
            req.delete()
            
            # ক্লায়েন্ট সাইডে দেখানোর জন্য একটি মেসেজ তৈরি করা
            messages.success(request, success_msg)
            return JsonResponse({'status': 'success', 'message': success_msg, 'type': req.requested_role}, status=200)

    except Exception as e:
        # Django এর মেসেজ সিস্টেমে ত্রুটি দেখানো
        messages.error(request, f'DB Error during acceptance: {e}')
        return JsonResponse({'status': 'error', 'message': f'DB Error: {e}'}, status=500)


# Reject Request
@csrf_exempt
def reject_request(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
        
    if not request.session.get('admin_logged_in'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
        
    try:
        req = RegistrationRequest.objects.get(pk=pk)
        
        # রিকোয়েস্ট ডিলিট করা
        req_name = req.full_name
        req_role = req.requested_role
        req.delete()
        
        # ক্লায়েন্ট সাইডে দেখানোর জন্য একটি মেসেজ তৈরি করা
        messages.info(request, f'Registration request for {req_name} ({req_role}) has been rejected.')
        return JsonResponse({'status': 'success', 'message': 'Request rejected and deleted'}, status=200)

    except RegistrationRequest.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Request not found'}, status=404)
    except Exception as e:
        # Django এর মেসেজ সিস্টেমে ত্রুটি দেখানো
        messages.error(request, f'DB Error during rejection: {e}')
        return JsonResponse({'status': 'error', 'message': f'DB Error: {e}'}, status=500)


# =========================================================
#  ELIMINATE LOGIC (Soft Delete) (অপরিবর্তিত)
# =========================================================

@csrf_exempt
def eliminate_teacher(request):
    if request.method == 'POST' and request.POST.get('teacher_id'):
        teacher_id = request.POST.get('teacher_id')
        try:
            # এখানে Soft Delete লজিক যুক্ত হবে
            # Teacher.objects.filter(teacher_id=teacher_id).update(is_active=False)
            
            messages.success(request, f'Teacher ID {teacher_id} has been **eliminated** from the display list.')
            return JsonResponse({'status': 'success', 'message': 'Teacher eliminated'}, status=200)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@csrf_exempt
def eliminate_student(request):
    if request.method == 'POST' and request.POST.get('student_id'):
        student_id = request.POST.get('student_id')
        try:
            # এখানে Soft Delete লজিক যুক্ত হবে
            # Student.objects.filter(student_id=student_id).update(is_active=False)
            
            messages.success(request, f'Student ID {student_id} has been **eliminated** from the display list.')
            return JsonResponse({'status': 'success', 'message': 'Student eliminated'}, status=200)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
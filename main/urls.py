# main/urls.py (চূড়ান্ত আপডেটেড ভার্সন সহ Admin Messages & Exam Routine)

from django.urls import path
from . import views

urlpatterns = [
    # Core Pages 
    path('', views.index, name='index'), 
    path('main-content/', views.main_content, name='main_content_page'), 
    path('admission/', views.admission_info_view, name='admission_page'), 
    path('apply/', views.apply_form_view, name='apply_form_page'),
    path('login/', views.login_view, name='login'),
    
    # Submission & Dashboard Paths 
    path('login/submit/', views.login_user, name='login_user'), 
    path('register_request/', views.registration_request_view, name='registration_request'), 
    
    # Dashboard URLS 
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('dashboard/student/', views.student_dashboard_view, name='student_dashboard'),
    
    # Logout URL (আগের ফিক্স)
    path('logout/', views.logout_user, name='logout_user'),
    
    # =========================================================
    # 🌟 নতুন STUDENT DASHBOARD AJAX URLS (Admin Messages & Routine)
    # =========================================================
    # 1. নির্দিষ্ট ছাত্রের মেসেজ লোড করার জন্য (Message from Admin)
    path('ajax/student/messages/', views.get_student_messages, name='ajax_student_messages'),
    # 2. সকলের জন্য পরীক্ষার রুটিন লোড করার জন্য (Exam Routine)
    path('ajax/student/exam_routine/', views.get_exam_routine, name='ajax_exam_routine'),
    
    # ✅ মার্কস আপডেট URLS (Save Actions)
    # 1. Class Teacher মার্কস সেভ করার জন্য
    path('dashboard/teacher/update_class_marks/<str:teacher_id>/', views.update_class_marks, name='update_class_marks'),
    
    # 2. Subject Teacher মার্কস সেভ করার জন্য
    path('dashboard/teacher/update_subject_marks/<str:teacher_id>/', views.update_subject_marks, name='update_subject_marks'),
    
    # 🚀 পুরাতন AJAX URL: ডাইনামিক স্টুডেন্ট ডেটা লোড করার জন্য (Student Details)
    path('dashboard/teacher/load_students/', views.load_dynamic_students, name='load_dynamic_students'),
    
    # 🟢 নতুন AJAX URL: মার্কস আপডেটের জন্য ডাইনামিক স্টুডেন্ট লোড করার জন্য
    path('ajax/load_marks_students/', views.load_students_for_mark_update, name='load_students_for_mark_update'),
    
    # =========================================================
    # 🎯 নতুন অ্যাসাইনমেন্ট URL যোগ করা হলো (Create Assignment Action)
    # =========================================================
    path('dashboard/teacher/create_assignment/<str:teacher_id>/', views.create_assignment, name='create_assignment'),
    
    # =========================================================
    # 🎯 নতুন ADMIN LIST URLS (Registered Teacher/Student)
    # =========================================================
    path('dashboard/admin/teachers/', views.registered_teachers_view, name='admin_teachers_list'),
    path('dashboard/admin/students/', views.registered_students_view, name='admin_students_list'),
    
    # ⭐ নতুন ADMIN REGISTRATION REQUEST URL
    path('dashboard/admin/registration-requests/', views.registration_requests_view, name='admin_registration_requests'),
    
    # 🟢 নতুন AJAX URLS: Registration Request Accept/Reject করার জন্য
    path('ajax/accept_request/<int:pk>/', views.accept_request, name='ajax_accept_request'),
    path('ajax/reject_request/<int:pk>/', views.reject_request, name='ajax_reject_request'),
    
    # =========================================================
    # 🚀 নতুন ADMIN MANAGEMENT URLS (Teacher Update / Student Management)
    # =========================================================
    path('dashboard/admin/teacher-update/', views.teacher_update_view, name='admin_teacher_update'),
    path('dashboard/admin/student-management/', views.student_management_view, name='admin_student_management'),
    
    # ⭐ নতুন ADMIN PAYMENT DETAIL URL
    path('dashboard/admin/payment-detail/', views.payment_detail_view, name='admin_payment_detail'),
    
    # 🚀 নতুন ELIMINATE ACTION URLS (AJAX for Soft Delete)
    path('ajax/eliminate_teacher/', views.eliminate_teacher, name='ajax_eliminate_teacher'),
    path('ajax/eliminate_student/', views.eliminate_student, name='ajax_eliminate_student'),
]
# main/admin.py (FIXED for E040 Error + Admin Message & Exam Routine ADDED)

from django.contrib import admin
# SubjectClassAssignment মডেলটি Admin প্যানেলে ব্যবহারের জন্য ইম্পোর্ট করা হলো
# ✅ নতুন মডেলগুলি ইম্পোর্ট করা হলো: AdminMessage, ExamSchedule
from .models import Teacher, Student, Subject, Mark, SubjectClassAssignment, AdminMessage, ExamSchedule 


# --- ১. Subject এর জন্য Admin কাস্টমাইজেশন (FIX: search_fields যোগ করা হলো) ---
class SubjectAdmin(admin.ModelAdmin):
    # এই ফিল্ডগুলো Subject Assignment Inline-এর Autocomplete-এর জন্য দরকার
    search_fields = ('subject_name', 'subject_code')

# --- ২. Subject Assignment Inline তৈরি করা ---
class SubjectAssignmentInline(admin.TabularInline):
    model = SubjectClassAssignment
    extra = 1 
    fields = ('class_sec', 'subject',) 
    autocomplete_fields = ['subject'] 
    verbose_name_plural = "Subject Teacher of: (Assigned Classes/Subjects)"


# --- ৩. Teacher মডেলের জন্য Admin কাস্টমাইজেশন ---
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'first_name', 'last_name', 'email', 'designation', 'class_teacher_of')
    search_fields = ('teacher_id', 'first_name', 'last_name', 'email')
    inlines = [SubjectAssignmentInline]


# =========================================================
# 🎯 FIX: Student Autocomplete ঠিক করার জন্য StudentAdmin তৈরি
# =========================================================
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'roll_number', 'first_name', 'last_name', 'class_name', 'section', 'payment_status')
    # AdminMessageAdmin-এ student ফিল্ডের autocomplete-এর জন্য এই search_fields আবশ্যক
    search_fields = ('student_id', 'roll_number', 'first_name', 'last_name')
    list_filter = ('class_name', 'section', 'payment_status')


# =========================================================
# 🎯 নতুন Admin ক্লাস: Admin Message এর জন্য (Student Autocomplete)
# =========================================================
class AdminMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'student', 'sent_at')
    # student ফিল্ডের জন্য Autocomplete যোগ করা হলো
    autocomplete_fields = ['student'] 
    # student__... ব্যবহার করে Student মডেলের ফিল্ডের মাধ্যমে সার্চ করা
    search_fields = ('subject', 'student__first_name', 'student__last_name', 'student__student_id')
    list_filter = ('sent_at',)

# =========================================================
# 🎯 নতুন Admin ক্লাস: Exam Schedule এর জন্য
# =========================================================
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_date')
    search_fields = ('title',)


# --- ৪. মডেলেগুলি রেজিস্টার করা ---

admin.site.register(Teacher, TeacherAdmin) 

# ✅ FIX: Student-কে নতুন কাস্টম ক্লাস দিয়ে রেজিস্টার করা হলো
admin.site.register(Student, StudentAdmin)

# ✅ FIX: Subject-কে নতুন কাস্টম ক্লাস দিয়ে রেজিস্টার করা হলো
admin.site.register(Subject, SubjectAdmin) 
admin.site.register(Mark)

# =========================================================
# ✅ নতুন মডেলগুলি রেজিস্টার করা হলো
# =========================================================
admin.site.register(AdminMessage, AdminMessageAdmin)
admin.site.register(ExamSchedule, ExamScheduleAdmin)
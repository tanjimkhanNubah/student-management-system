# main/models.py (FINAL UPDATED)

from django.db import models
from django.contrib.auth.hashers import make_password 
from django.utils import timezone # ✅ FIX: timezone আমদানী করা হলো

# --- বিদ্যমান Teacher মডেল (UPDATED: is_active যোগ করা হলো) ---
class Teacher(models.Model):
    teacher_id = models.CharField(max_length=10, unique=True, primary_key=True) 
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    phone = models.CharField(max_length=15)
    
    password = models.CharField(max_length=128) 
    
    designation = models.CharField(max_length=100, default='Teacher') 
    subject_taught = models.CharField(max_length=100) 
    class_teacher_of = models.CharField(max_length=50, blank=True, null=True) 
    
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)
    schedule_details = models.TextField(blank=True, null=True) 
    
    joining_date = models.DateField(auto_now_add=True) 
    
    # 🎯 নতুন ফিল্ড: সফট ডিলিটের জন্য
    is_active = models.BooleanField(default=True) 

    def __str__(self):
        return f"{self.teacher_id} - {self.first_name} {self.last_name}"

    class Meta:
        ordering = ['teacher_id']

# --- নতুন Student মডেল (UPDATED: is_active যোগ করা হলো) ---
class Student(models.Model):
    student_id = models.CharField(max_length=10, unique=True, primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    roll_number = models.IntegerField() 
    
    class_name = models.CharField(max_length=10)
    section = models.CharField(max_length=5)
    
    father_name = models.CharField(max_length=100, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    
    password = models.CharField(max_length=128) 
    
    joining_date = models.DateField(auto_now_add=True)
    
    # 💡 নতুন ফিল্ড: পেমেন্ট স্ট্যাটাস ডাইনামিকালি দেখানোর জন্য
    PAYMENT_CHOICES = [
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
        ('Pending', 'Pending'),
        ('Unknown', 'Unknown'), # আপনার default এর সাথে মিল রেখে যোগ করা হলো
    ]
    payment_status = models.CharField(
        max_length=10, 
        choices=PAYMENT_CHOICES, 
        default='Unknown',
    )
    
    # 🎯 নতুন ফিল্ড: সফট ডিলিটের জন্য
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student_id} - {self.first_name} ({self.class_name}{self.section})"

    class Meta:
        ordering = ['roll_number']
        unique_together = ('class_name', 'section', 'roll_number')

# --- নতুন Subject মডেল (কোনো পরিবর্তন নেই) ---
class Subject(models.Model):
    subject_name = models.CharField(max_length=100, unique=True)
    subject_code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.subject_name
        
# --- নতুন Mark মডেল (কোনো পরিবর্তন নেই) ---
class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    
    ot_marks = models.IntegerField(default=0)
    ct_marks = models.IntegerField(default=0)
    obtained_marks = models.IntegerField(default=0)
    
    exam_type = models.CharField(max_length=50, default='Midterm')
    
    # 💡 নতুন প্রপার্টি: স্বয়ংক্রিয়ভাবে এভারেজ গণনা করা হবে
    @property
    def average_marks(self):
        """
        Average = OT + CT + (Obtained Marks * 0.8)
        """
        
        # 1. Obtained Marks কে 80% এ রূপান্তর করা
        obtained_80_percent = self.obtained_marks * 0.8
        
        # 2. মোট এভারেজ গণনা
        total_average = self.ot_marks + self.ct_marks + obtained_80_percent
        
        # দশমিকের পর দুটি সংখ্যা রাখা
        return round(total_average, 2)
    
    class Meta:
        unique_together = (('student', 'subject', 'exam_type'),)
        ordering = ['student', 'subject__subject_code']

    def __str__(self):
        return f"{self.student.first_name} - {self.subject.subject_name} Marks"

# --- SubjectClassAssignment মডেল (কোনো পরিবর্তন নেই) ---
class SubjectClassAssignment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    class_sec = models.CharField(max_length=50) 
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE) 

    class Meta:
        unique_together = ('teacher', 'class_sec', 'subject')

    def __str__(self):
        return f"{self.subject.subject_name} for {self.class_sec}"


# =========================================================
#  🎯 নতুন Assignment মডেল (কোনো পরিবর্তন নেই)
# =========================================================

class Assignment(models.Model):
    # যে শিক্ষক অ্যাসাইনমেন্টটি দিয়েছেন
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE) 
    
    # যে ক্লাসের জন্য অ্যাসাইনমেন্টটি দেওয়া হয়েছে (যেমন: 5A, 8C)
    # class_sec স্ট্রিং আকারে না রেখে class_name ও section আলাদা রাখা হলো
    class_name = models.CharField(max_length=10)
    section = models.CharField(max_length=10)
    
    # অ্যাসাইনমেন্টের বিষয়বস্তু
    title = models.CharField(max_length=150)
    description = models.TextField()
    
    # অ্যাসাইনমেন্ট জমা দেওয়ার শেষ তারিখ
    due_date = models.DateField()
    
    # কখন অ্যাসাইনমেন্টটি তৈরি করা হয়েছে
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assignment for {self.class_name}{self.section}: {self.title}"

    class Meta:
        # অ্যাসাইনমেন্ট জমা দেওয়ার তারিখ অনুযায়ী সাজানো হবে
        ordering = ['due_date', 'class_name', 'section']


# =========================================================
#  ✅ নতুন RegistrationRequest মডেল (FIXED: phone_number যোগ করা হলো)
# =========================================================

class RegistrationRequest(models.Model):
    ROLE_CHOICES = [
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
        ('Admin', 'Admin'), # Admin রিকোয়েস্ট থাকলেও রাখলাম
    ]

    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    requested_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    # 🎯 FIX: phone_number যোগ করা হলো
    phone_number = models.CharField(max_length=15, blank=True, null=True) 
    
    # Student-এর জন্য অতিরিক্ত ফিল্ড (Teacher-এর ক্ষেত্রে এগুলি ফাঁকা থাকবে)
    class_name = models.CharField(max_length=10, blank=True, null=True)
    section = models.CharField(max_length=5, blank=True, null=True)
    roll_no = models.CharField(max_length=10, blank=True, null=True) 
    
    # রিকোয়েস্টের অবস্থা
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    
    # কখন রিকোয়েস্টটি করা হয়েছে
    requested_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.requested_role == 'Teacher':
            return f"Request from {self.full_name} ({self.requested_role}) - Status: {self.status}"
        return f"Request from {self.full_name} ({self.requested_role} - {self.class_name}{self.section}/{self.roll_no}) - Status: {self.status}"

    class Meta:
        ordering = ['-requested_at']

# =========================================================
# 🎯 নতুন মডেল ১: Admin Message (নির্দিষ্ট ছাত্রকে বার্তা পাঠানোর জন্য)
# =========================================================
class AdminMessage(models.Model):
    # স্টুডেন্টকে ফরেন কী হিসেবে যুক্ত করা যাতে এটি নির্দিষ্ট ছাত্রের সাথে লিঙ্ক করা যায়
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='admin_messages')
    
    subject = models.CharField(max_length=200)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message for {self.student.first_name} {self.student.last_name} - {self.subject}"

    class Meta:
        verbose_name = "Admin Message (Per Student)"
        verbose_name_plural = "Admin Messages (Per Student)"
        ordering = ['-sent_at']


# =========================================================
# 🎯 নতুন মডেল ২: Exam Schedule (সকল ছাত্রের জন্য একই রুটিন)
# =========================================================
class ExamSchedule(models.Model):
    title = models.CharField(max_length=200, help_text="যেমন: 'First Term Examination 2024'")
    
    # রুটিনটি ছবি বা PDF ফাইল হিসেবে আপলোড করা যেতে পারে
    file = models.FileField(upload_to='exam_routines/') 
    
    published_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Exam Routine (Common)"
        verbose_name_plural = "Exam Routines (Common)"
        ordering = ['-published_date']
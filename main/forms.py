from django import forms

class AdmissionApplicationForm(forms.Form):
    applicant_name = forms.CharField(label='Full Name of Applicant', max_length=100)
    father_name = forms.CharField(label="Father's Name", max_length=100)
    mother_name = forms.CharField(label="Mother's Name", max_length=100)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Date of Birth")
    grade_applying_for = forms.ChoiceField(
        choices=[('KG', 'Kindergarten'), ('C1', 'Class 1'), ('C2', 'Class 2')],
        label='Applying For Grade'
    )
    email = forms.EmailField(label='Email Address')
    phone = forms.CharField(label='Phone Number', max_length=15)
from django import forms
from django.utils import timezone
from AuthApp.models import User
from EmployeeApp.models import Course
from StudentApp.models import (
    Enrollment, ExamResult, Certificate, GuardianReport, FeePayment
)


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ('course', 'status', 'fee_paid')


class ExamResultForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = ('enrollment', 'exam_name', 'marks_obtained', 'total_marks', 'passed', 'remarks')


class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ('course', 'certificate_type')


class GuardianReportForm(forms.ModelForm):
    class Meta:
        model = GuardianReport
        fields = ('report_type', 'content', 'sent_to')


class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = ('enrollment', 'amount', 'due_date', 'status', 'payment_method', 'transaction_id')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
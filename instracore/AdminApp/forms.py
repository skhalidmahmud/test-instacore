from django import forms
from django.contrib.auth.forms import UserCreationForm
from AuthApp.models import User
from AdminApp.models import Event, Notice, WeekendCalendar, FinancialOverview


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'sub_role', 
                  'image', 'bio', 'date_of_birth', 'phone', 'gender', 'location', 'country',
                  'facebook', 'twitter', 'instagram', 'linkedin')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_role'].required = False
    
    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'sub_role', 
                  'image', 'bio', 'date_of_birth', 'phone', 'gender', 'location', 'country',
                  'facebook', 'twitter', 'instagram', 'linkedin', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_role'].required = False


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ('title', 'description', 'category', 'date', 'start_time', 'end_time', 'location', 'is_active')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ('title', 'content', 'category', 'priority', 'expiry_date', 'is_active')
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }


class WeekendCalendarForm(forms.ModelForm):
    class Meta:
        model = WeekendCalendar
        fields = ('date', 'is_weekend', 'description')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class FinancialOverviewForm(forms.ModelForm):
    class Meta:
        model = FinancialOverview
        fields = ('month', 'income', 'expenses', 'fees_collected', 'salaries_paid')
        widgets = {
            'month': forms.DateInput(attrs={'type': 'month'}),
        }
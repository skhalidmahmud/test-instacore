from django.db import models
from AuthApp.models import User


class Event(models.Model):
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('cultural', 'Cultural'),
        ('sports', 'Sports'),
        ('holiday', 'Holiday'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="events")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


class Notice(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('academic', 'Academic'),
        ('emergency', 'Emergency'),
        ('event', 'Event'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="notices")
    is_active = models.BooleanField(default=True)


class WeekendCalendar(models.Model):
    date = models.DateField(unique=True)
    is_weekend = models.BooleanField(default=True)
    description = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.date} - {'Weekend' if self.is_weekend else 'Holiday'}"


class FinancialOverview(models.Model):
    month = models.DateField()
    income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    fees_collected = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    salaries_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('month',)
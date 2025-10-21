from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

# The project Model
class Project(models.Model):
    HEALTH_CHOICES = [
        ('good', 'Good'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    team_roster = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='team_projects', blank=True)

    progress = models.PositiveIntegerField(default=0)
    health = models.CharField(max_length=10, choices=HEALTH_CHOICES, default='good')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    tags = models.JSONField(default=list, blank=True)

    deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    # Calculated the progress of the project
    def calculate_progress(self):
        # if the project hasn't been saved yet we skip
        if not self.pk:
            return 0
        milestones = self.milestones.all()
        if not milestones:
            return 0
        completed = milestones.filter(completed=True).count()
        return int((completed / milestones.count()) * 100)

    def calculate_health(self):
        """
        Calculate project health based on multiple factors:
        - Progress percentage
        - Overdue milestones
        - Project timeline
        - Recent activity
        """
        if not self.pk:
            return 'good'
        
        milestones = self.milestones.all()
        if not milestones:
            return 'good'
        
        # Calculate progress
        progress = self.calculate_progress()
        
        # Check for overdue milestones
        today = timezone.now().date()
        overdue_milestones = milestones.filter(
            due_date__lt=today,
            completed=False
        ).count()
        
        # Check for upcoming deadlines (within 7 days)
        upcoming_deadline = timezone.now().date() + timedelta(days=7)
        upcoming_milestones = milestones.filter(
            due_date__lte=upcoming_deadline,
            due_date__gte=today,
            completed=False
        ).count()
        
        # Health calculation logic
        if progress >= 90 and overdue_milestones == 0:
            return 'good'
        elif progress >= 70 and overdue_milestones <= 1:
            return 'good'
        elif progress >= 50 and overdue_milestones <= 2:
            return 'warning'
        elif progress >= 30 and overdue_milestones <= 3:
            return 'warning'
        else:
            return 'critical'

    def save(self, *args, **kwargs):
        self.progress = self.calculate_progress()
        self.health = self.calculate_health()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

# The milestone model
class Milestone(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_milestones')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Set completed_date when milestone is marked as completed
        if self.completed and not self.completed_date:
            self.completed_date = timezone.now().date()
        elif not self.completed:
            self.completed_date = None
        
        super().save(*args, **kwargs)
        
        # Update project progress and health when milestone is saved
        if self.project:
            self.project.progress = self.project.calculate_progress()
            self.project.health = self.project.calculate_health()
            self.project.save(update_fields=['progress', 'health'])

    def is_overdue(self):
        """Check if milestone is overdue"""
        if not self.due_date or self.completed:
            return False
        return self.due_date < timezone.now().date()

    def is_due_soon(self, days=7):
        """Check if milestone is due within specified days"""
        if not self.due_date or self.completed:
            return False
        due_soon_date = timezone.now().date() + timedelta(days=days)
        return self.due_date <= due_soon_date

    def __str__(self):
        return f"{self.name} ({'done' if self.completed else 'pending'})"

from django.db import models
from django.conf import settings

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
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')

    progress = models.PositiveIntegerField(default=0)
    health = models.CharField(max_length=10, choices=HEALTH_CHOICES, default='good')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    tags = models.JSONField(default=list, blank=True)

    deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    # Calculated the progress of the project
    def calculate_progress(self):
        milestones = self.milestones.all()
        if not milestones:
            return 0
        completed = milestones.filter(completed=True).count()
        return int((completed / milestones.count()) * 100)

    ''' 
    Calculates the health or the project
    For the time being we calculate it based on progress
    Todo: implement health calculation logic
    '''
    
    def calculate_health(self):
        if self.progress >= 80:
            return 'good'
        elif self.progress >= 50:
            return 'warning'
        return 'critical'

    def save(self, *args, **kwargs):
        self.progress = self.calculate_progress()
        self.health = self.calculate_health()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

# The milestone model
class Milestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({'done' if self.completed else 'pending'})"

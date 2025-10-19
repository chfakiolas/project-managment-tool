from rest_framework import serializers
from .models import Project, Milestone

# Handles simple CRUD for milestones
class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ['id', 'name', 'completed', 'due_date']
   
# Handles CRUD for projects and includes milestones inline     
class ProjectSerializer(serializers.ModelSerializer):
    # We nest the milestones inside the project responses
    milestones = MilestoneSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'description',
            'owner',
            'owner_name',
            'progress',
            'health',
            'status',
            'tags',
            'deleted',
            'created_at',
            'last_updated',
            'milestones',
        ]
        read_only_fields = ['progress', 'health', 'created_at', 'last_updated']
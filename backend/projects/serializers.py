from rest_framework import serializers
from .models import Project, Milestone

# Handles CRUD for milestones with enhanced fields
class MilestoneSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    is_due_soon = serializers.SerializerMethodField()
    
    class Meta:
        model = Milestone
        fields = [
            'id', 
            'name', 
            'description',
            'completed', 
            'due_date',
            'completed_date',
            'priority',
            'assigned_to',
            'assigned_to_name',
            'created_at',
            'updated_at',
            'is_overdue',
            'is_due_soon'
        ]
        read_only_fields = ['completed_date', 'created_at', 'updated_at']
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()
    
    def get_is_due_soon(self, obj):
        return obj.is_due_soon()
   
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
# from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from .models import Project, Milestone
from .serializers import ProjectSerializer, MilestoneSerializer
from django_filters.rest_framework import DjangoFilterBackend

# this handles all CRUD operations for project and also soft delete, restore, and bulk update.
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.filter(deleted=False).order_by('-last_updated')
    serializer_class = ProjectSerializer
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # search fields 
    search_fields = ['title', 'description']
    # filter fields
    filterset_fields = ['status', 'owner', 'health']


    # we override delete to softdelete 
    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        project.deleted = True
        project.save()
        return Response({"status": "project soft-deleted"}, status=status.HTTP_204_NO_CONTENT)

    # recover soft deleted project
    @action(detail=True, methods=['post'])
    def recover(self, request, pk=None):
        project = Project.objects.get(pk=pk)
        project.deleted = False
        project.last_updated = timezone.now()
        project.save()
        return Response({"status": "project recovered"})

    # bulk update action
    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """
        this expects a JSON for example:
        { 
            "ids": [1,2,3], // the projects we want to update
            "status": "on_hold" // the bulk status we will set
        }
        """
        ids = request.data.get('ids', [])
        status_value = request.data.get('status')

        with transaction.atomic():
            updated = Project.objects.filter(id__in=ids).update(status=status_value, last_updated=timezone.now())

        return Response({"updated": updated, "status": status_value})


class MilestoneViewSet(viewsets.ModelViewSet):
    # CRUD for Milestones each belongs to a project
    queryset = Milestone.objects.all().order_by('due_date')
    serializer_class = MilestoneSerializer

    def perform_create(self, serializer):
        serializer.save()
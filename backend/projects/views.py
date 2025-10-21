# from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from .models import Project, Milestone
from .serializers import ProjectSerializer, MilestoneSerializer
from django_filters.rest_framework import DjangoFilterBackend

# this handles all CRUD operations for project and also soft delete, restore, and bulk update.
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.filter(deleted=False).order_by('-last_updated')
    serializer_class = ProjectSerializer
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # Enhanced search fields - now includes tags for better search
    search_fields = ['title', 'description', 'tags']
    # filter fields
    filterset_fields = ['status', 'owner', 'health']
    # ordering fields
    ordering_fields = ['title', 'created_at', 'last_updated', 'progress', 'health']
    ordering = ['-last_updated']


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

    # permanently delete a project
    @action(detail=True, methods=['delete'])
    def permanent_delete(self, request, pk=None):
        project = Project.objects.get(pk=pk)
        project.delete()  # This will permanently delete the project
        return Response({"status": "project permanently deleted"})

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

    # Get deleted projects
    @action(detail=False, methods=['get'])
    def deleted_projects(self, request):
        """
        Retrieve all soft-deleted projects with pagination
        """
        # Get deleted projects
        queryset = Project.objects.filter(deleted=True).order_by('-last_updated')
        
        # Apply search if provided
        search_query = request.query_params.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(tags__icontains=search_query)
            )
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        health_filter = request.query_params.get('health')
        if health_filter:
            queryset = queryset.filter(health=health_filter)
        
        # Apply ordering
        ordering = request.query_params.get('ordering', '-last_updated')
        queryset = queryset.order_by(ordering)
        
        # Paginate results
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 12))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        results = queryset[start:end]
        
        # Serialize results
        serializer = self.get_serializer(results, many=True)
        
        return Response({
            'results': serializer.data,
            'count': total_count,
            'next': f"?page={page + 1}" if end < total_count else None,
            'previous': f"?page={page - 1}" if page > 1 else None,
            'current_page': page,
            'total_pages': (total_count + page_size - 1) // page_size
        })

    # Advanced search action
    @action(detail=False, methods=['get'])
    def advanced_search(self, request):
        """
        Advanced search with multiple criteria:
        - search: free text search across title, description, and tags
        - status: filter by project status
        - owner: filter by project owner
        - health: filter by project health
        - tags: filter by specific tags (comma-separated)
        - ordering: sort by field (prefix with - for descending)
        """
        search_query = request.query_params.get('search', '')
        status_filter = request.query_params.get('status')
        owner_filter = request.query_params.get('owner')
        health_filter = request.query_params.get('health')
        tags_filter = request.query_params.get('tags', '')
        ordering = request.query_params.get('ordering', '-last_updated')
        
        # Start with base queryset
        queryset = Project.objects.filter(deleted=False)
        
        # Apply search query
        if search_query:
            # Search across title, description, and tags
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(tags__icontains=search_query)
            )
        
        # Apply filters
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if owner_filter:
            queryset = queryset.filter(owner=owner_filter)
        if health_filter:
            queryset = queryset.filter(health=health_filter)
        if tags_filter:
            # Handle multiple tags (comma-separated)
            tag_list = [tag.strip() for tag in tags_filter.split(',') if tag.strip()]
            for tag in tag_list:
                queryset = queryset.filter(tags__icontains=tag)
        
        # Apply ordering
        queryset = queryset.order_by(ordering)
        
        # Paginate results
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 12))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        results = queryset[start:end]
        
        # Serialize results
        serializer = self.get_serializer(results, many=True)
        
        return Response({
            'results': serializer.data,
            'count': total_count,
            'next': f"?page={page + 1}" if end < total_count else None,
            'previous': f"?page={page - 1}" if page > 1 else None,
            'current_page': page,
            'total_pages': (total_count + page_size - 1) // page_size
        })


class MilestoneViewSet(viewsets.ModelViewSet):
    # CRUD for Milestones each belongs to a project
    queryset = Milestone.objects.all().order_by('due_date')
    serializer_class = MilestoneSerializer

    def perform_create(self, serializer):
        serializer.save()
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, MilestoneViewSet, get_users

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'milestones', MilestoneViewSet, basename='milestone')

urlpatterns = [
    path('', include(router.urls)),
    path('users/', get_users, name='users'),
]
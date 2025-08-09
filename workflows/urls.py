"""
URLs for workflows app
"""
from django.urls import path
from . import views

app_name = 'workflows'

urlpatterns = [
    # Approval Requests
    path('pending/', views.pending_approvals, name='pending'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('history/', views.approval_history, name='history'),
    
    # Request Operations
    path('request/<uuid:request_id>/', views.request_detail, name='request_detail'),
    path('request/<uuid:request_id>/approve/', views.approve_request, name='approve'),
    path('request/<uuid:request_id>/reject/', views.reject_request, name='reject'),
    path('request/<uuid:request_id>/delegate/', views.delegate_request, name='delegate'),
    path('request/<uuid:request_id>/cancel/', views.cancel_request, name='cancel'),
    
    # Workflow Management
    path('workflows/', views.workflow_list, name='workflows'),
    path('workflows/add/', views.add_workflow, name='add_workflow'),
    path('workflows/<uuid:workflow_id>/', views.workflow_detail, name='workflow_detail'),
    path('workflows/<uuid:workflow_id>/edit/', views.edit_workflow, name='edit_workflow'),
    path('workflows/<uuid:workflow_id>/delete/', views.delete_workflow, name='delete_workflow'),
    
    # Workflow Templates
    path('templates/', views.template_list, name='templates'),
    path('templates/add/', views.add_template, name='add_template'),
    path('templates/<int:template_id>/', views.template_detail, name='template_detail'),
    path('templates/<int:template_id>/edit/', views.edit_template, name='edit_template'),
    path('templates/<int:template_id>/clone/', views.clone_template, name='clone_template'),
    
    # Reports
    path('reports/', views.workflow_reports, name='reports'),
    path('reports/performance/', views.performance_report, name='performance_report'),
    path('reports/bottlenecks/', views.bottleneck_report, name='bottleneck_report'),
    path('reports/export/', views.export_workflow_data, name='export'),
    
    # API endpoints
    path('api/step-status/<uuid:request_id>/', views.step_status, name='step_status'),
    path('api/escalate/<uuid:request_id>/', views.escalate_request, name='escalate'),
]
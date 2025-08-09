"""
URLs for security app
"""
from django.urls import path
from . import views

app_name = 'security'

urlpatterns = [
    # Audit Logs
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('audit-logs/export/', views.export_audit_logs, name='export_audit_logs'),
    path('audit-logs/detail/<uuid:log_id>/', views.audit_log_detail, name='audit_log_detail'),
    
    # User Sessions
    path('sessions/', views.active_sessions, name='sessions'),
    path('sessions/my/', views.my_sessions, name='my_sessions'),
    path('sessions/<int:session_id>/terminate/', views.terminate_session, name='terminate_session'),
    
    # Login Attempts
    path('login-attempts/', views.login_attempts, name='login_attempts'),
    path('login-attempts/failed/', views.failed_login_attempts, name='failed_attempts'),
    
    # Security Reports
    path('reports/', views.security_reports, name='reports'),
    path('reports/daily/', views.daily_security_report, name='daily_report'),
    path('reports/weekly/', views.weekly_security_report, name='weekly_report'),
    path('reports/monthly/', views.monthly_security_report, name='monthly_report'),
    
    # Security Settings
    path('settings/', views.security_settings, name='settings'),
    path('settings/password-policy/', views.password_policy, name='password_policy'),
    path('settings/session-config/', views.session_config, name='session_config'),
    
    # Two-Factor Authentication
    path('2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('2fa/verify/', views.verify_2fa, name='verify_2fa'),
    path('2fa/disable/', views.disable_2fa, name='disable_2fa'),
    
    # Security Incidents
    path('incidents/', views.security_incidents, name='incidents'),
    path('incidents/add/', views.add_incident, name='add_incident'),
    path('incidents/<uuid:incident_id>/', views.incident_detail, name='incident_detail'),
    path('incidents/<uuid:incident_id>/update/', views.update_incident, name='update_incident'),
]
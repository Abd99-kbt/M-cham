"""
URLs for accounts app
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    
    # AJAX endpoints
    path('get-positions-by-department/', views.get_positions_by_department, name='get_positions_by_department'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('settings/', views.user_settings, name='settings'),
    
    # User Management (Admin only)
    path('users/', views.user_list, name='users'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/<int:user_id>/permissions/', views.user_permissions, name='user_permissions'),
    
    # Departments
    path('departments/', views.department_list, name='departments'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/debug/', views.debug_department_form, name='debug_department_form'),
    path('departments/<int:dept_id>/', views.department_detail, name='department_detail'),
    path('departments/<int:dept_id>/edit/', views.edit_department, name='edit_department'),
    
    # Positions
    path('positions/', views.position_list, name='positions'),
    path('positions/add/', views.add_position, name='add_position'),
    path('positions/<int:pos_id>/edit/', views.edit_position, name='edit_position'),
    
    # Groups
    path('groups/', views.group_list, name='groups'),
    path('groups/add/', views.add_group, name='add_group'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/edit/', views.edit_group, name='edit_group'),
    
    # Delegation
    path('delegation/', views.delegation_view, name='delegation'),
    path('delegation/create/', views.create_delegation, name='create_delegation'),
    path('delegation/<int:delegation_id>/end/', views.end_delegation, name='end_delegation'),

    # Admin Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/add/', views.admin_add_user, name='admin_add_user'),
    path('admin/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin/users/<int:user_id>/toggle/', views.admin_toggle_user, name='admin_toggle_user'),
    path('admin/users/<int:user_id>/reset-password/', views.admin_reset_password, name='admin_reset_password'),
    path('admin/users/<int:user_id>/activity/', views.admin_user_activity, name='admin_user_activity'),
]
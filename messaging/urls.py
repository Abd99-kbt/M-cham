"""
URLs for messaging app
"""
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Message Lists
    path('inbox/', views.inbox, name='inbox'),
    path('sent/', views.sent_messages, name='sent'),
    path('drafts/', views.drafts, name='drafts'),
    path('archive/', views.archive, name='archive'),
    
    # Message Operations
    path('compose/', views.compose_message, name='compose'),
    path('message/<uuid:message_id>/', views.message_detail, name='message_detail'),
    path('message/<uuid:message_id>/reply/', views.reply_message, name='reply'),
    path('message/<uuid:message_id>/forward/', views.forward_message, name='forward'),
    path('message/<uuid:message_id>/delete/', views.delete_message, name='delete'),
    path('message/<uuid:message_id>/archive/', views.archive_message, name='archive_message'),
    path('message/<uuid:message_id>/unarchive/', views.unarchive_message, name='unarchive_message'),
    
    # AJAX endpoints
    path('api/unread-count/', views.unread_count, name='unread_count'),
    path('api/mark-read/<uuid:message_id>/', views.mark_as_read, name='mark_read'),
    path('api/save-draft/', views.save_draft, name='save_draft'),
    path('api/search/', views.search_messages, name='search'),
    
    # Categories
    path('categories/', views.category_list, name='categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:cat_id>/edit/', views.edit_category, name='edit_category'),
    
    # Reports
    path('reports/', views.message_reports, name='reports'),
    path('reports/export/', views.export_messages, name='export'),
    
    # Attachments
    path('attachment/<int:attachment_id>/download/', views.download_attachment, name='download_attachment'),
    path('attachment/<int:attachment_id>/view/', views.view_attachment, name='view_attachment'),
    
    # Digital Signature
    path('verify-signature/<uuid:signature_id>/', views.verify_signature_view, name='verify_signature'),
    path('signature/<uuid:signature_id>/qr/', views.signature_qr_image, name='signature_qr'),
    path('signature/<uuid:signature_id>/certificate/', views.signature_certificate, name='signature_certificate'),
    
    # Testing and Debug
    path('test-editor/', views.test_editor, name='test_editor'),
    path('debug-tinymce/', views.debug_tinymce, name='debug_tinymce'),
    path('simple-test/', views.simple_test, name='simple_test'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_form, name='student_form'),
    path('grades/', views.grades_list, name='grades_list'),
    path('upload/', views.upload_xml, name='upload_xml'),
    path('files/', views.xml_files_list, name='xml_files_list'),
    path('files/<str:filename>/', views.view_xml_file, name='view_xml_file'),
    path('download/<str:filename>/', views.download_xml_file, name='download_xml_file'),
    path('ajax-search/', views.ajax_search, name='ajax_search'),
    path('edit/<int:grade_id>/', views.edit_grade, name='edit_grade'),
    path('delete/<int:grade_id>/', views.delete_grade, name='delete_grade')
]
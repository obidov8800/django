# tests/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.test_list_view, name='test_list'),
    path('take/<int:test_id>/', views.take_test_view, name='take_test'),
    path('result/<int:result_id>/', views.test_result_detail_view, name='test_result_detail'),
    path('export-results-pdf/', views.export_results_pdf_view, name='export_results_pdf'),
    path('<int:test_id>/import-questions/', views.import_questions_from_file_view, name='import_questions'), # YANGI QATOR
]
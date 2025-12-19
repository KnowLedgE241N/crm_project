from django.urls import path
from .views import forms_page, form_create, form_fill, form_results, form_delete,fields_reorder
from .views_questions import questions_list, question_add, question_edit, question_delete



urlpatterns = [
    path("forms/", forms_page, name="forms_page"),
    path("forms/new/", form_create, name="form_create"),
    path("forms/<int:pk>/fill/", form_fill, name="form_fill"),
    path("forms/<int:pk>/results/", form_results, name="form_results"),
    path("forms/<int:pk>/questions/", questions_list, name="questions_list"),
    path("forms/<int:pk>/questions/new/", question_add, name="question_add"),
    path("forms/<int:pk>/questions/<int:field_id>/edit/", question_edit, name="question_edit"),
    path("forms/<int:pk>/questions/<int:field_id>/delete/", question_delete, name="question_delete"),
    path("forms/<int:pk>/delete/", form_delete, name="form_delete"),
    path("forms/<int:pk>/fields/reorder/", fields_reorder, name="fields_reorder"),
    



]





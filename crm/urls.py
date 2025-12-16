from django.urls import path
from .views import healthcheck_create
from .views_tables import tables_page, table_add_record, table_edit_record, table_delete_record
from .views_tables import table_row_display, table_row_edit, table_row_save
from .views_graphs import graphs_page, graphs_data

urlpatterns = [
    path("health-checks/new/", healthcheck_create, name="healthcheck_create"),
    path("tables/", tables_page, name="tables_page"),
    path("tables/<str:table_key>/add/", table_add_record, name="table_add_record"),
    path("tables/<str:table_key>/<int:pk>/edit/", table_edit_record, name="table_edit_record"),
    path("tables/<str:table_key>/<int:pk>/delete/", table_delete_record, name="table_delete_record"),
    path("tables/<str:table_key>/<int:pk>/row/", table_row_display, name="table_row_display"),
    path("tables/<str:table_key>/<int:pk>/row/edit/", table_row_edit, name="table_row_edit"),
    path("tables/<str:table_key>/<int:pk>/row/save/", table_row_save, name="table_row_save"),
    path("graphs/", graphs_page, name="graphs_page"),
    path("graphs/data/", graphs_data, name="graphs_data"),
]



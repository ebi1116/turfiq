from django.urls import path
from .views import *
urlpatterns=[path("", ExpenseListView.as_view(), name="expense-list"), path("add/", ExpenseCreateView.as_view(), name="expense-add"), path("<int:pk>/edit/", ExpenseUpdateView.as_view(), name="expense-edit"), path("<int:pk>/delete/", ExpenseDeleteView.as_view(), name="expense-delete")]

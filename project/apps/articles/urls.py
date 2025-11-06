from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='articles'),
    path('create/', views.ArticleCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.ArticleDetailView.as_view(), name='article'),
    path('<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='edit'),
    path('<slug:slug>/delete/', views.ArticleDeleteView.as_view(), name='delete'),
    path('<slug:slug>/comment/', views.CommentCreateView.as_view(), name='comment_create'),
    path('comment/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
]
from django.views.generic import ListView, DetailView
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Article, Comment
from .forms import ArticleForm


class ArticleListView(ListView):
    model = Article
    template_name = 'articles/articles.html'
    context_object_name = 'articles'
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff:
            context['form'] = ArticleForm()
        return context


class ArticleCreateView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request):
        form = ArticleForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect('articles:articles')


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/article.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.get_object()
        context['comments'] = article.comments.filter(parent__isnull=True)
        return context


class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        parent_id = request.POST.get('parent_id')
        text = request.POST.get('text')
        if text:
            Comment.objects.create(
                user=request.user,
                article=article,
                text=text,
                parent_id=parent_id if parent_id else None
            )
        return redirect(reverse('articles:article', args=[slug]))


class CommentDeleteView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        article_slug = comment.article.slug
        comment.delete()
        return redirect(reverse('articles:article', args=[article_slug]))

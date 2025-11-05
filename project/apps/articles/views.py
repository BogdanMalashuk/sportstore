from django.views.generic import ListView, DetailView
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Article, Comment
from .forms import ArticleForm
from django.http import HttpResponse
from django.template.loader import render_to_string


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
    template_name = "articles/article_form.html"

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        form = ArticleForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = ArticleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("articles:articles")
        return render(request, self.template_name, {"form": form})


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/article.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.get_object()
        context['comments'] = article.comments.all()
        return context


class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        text = request.POST.get('text')
        if text:
            Comment.objects.create(user=request.user, article=article, text=text)

        # AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(
                'articles/comments.html',
                {'comments': article.comments.all()},
                request=request
            )
            return HttpResponse(html)

        return redirect(reverse('articles:article', args=[slug]))


class CommentDeleteView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        article_slug = comment.article.slug
        comment.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            article = get_object_or_404(Article, slug=article_slug)
            html = render_to_string(
                'articles/comments.html',
                {'comments': article.comments.all()},
                request=request
            )
            return HttpResponse(html)

        return redirect(reverse('articles:article', args=[article_slug]))

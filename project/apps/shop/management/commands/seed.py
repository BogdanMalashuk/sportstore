from django.core.management.base import BaseCommand
from apps.shop.models import Category, Product, Favorite, CartItem, Order, OrderItem
from apps.reviews.models import Review, Like
from apps.articles.models import Article, Comment
from apps.users.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker
import random

fake = Faker('ru_RU')


def generate_unique_slug_for_category(name):
    base_slug = slugify(name) or "category"
    slug = base_slug
    i = 1
    while Category.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{i}"
        i += 1
    return slug


def generate_unique_slug_for_article(title):
    base_slug = slugify(title) or "article"
    slug = base_slug
    i = 1
    while Article.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{i}"
        i += 1
    return slug


class Command(BaseCommand):
    help = "Заполняет базу тестовыми данными"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Начинаем заполнение базы...")

        # --- Очистка таблиц ---
        Like.objects.all().delete()
        Comment.objects.all().delete()
        Article.objects.all().delete()
        Review.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CartItem.objects.all().delete()
        Favorite.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()
        self.stdout.write("✅ Старые данные очищены.")

        # --- Пользователи ---
        users = [
            User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="123456",
                is_admin=(i == 0),
            )
            for i in range(1, 6)
        ]

        # --- Категории ---
        category_data = {
            "Протеины": [
                "Сывороточный протеин",
                "Казеиновый протеин",
                "Мультикомпонентный протеин",
                "Изолят протеина"
            ],
            "Креатины": [
                "Креатин моногидрат",
                "Креатин HCL",
                "Креатин капсулы",
                "Креатин порошок"
            ],
            "Жиросжигатели": [
                "Термогенные жиросжигатели",
                "L-карнитин",
                "CLA (линолевая кислота)",
                "Экстракт зелёного чая"
            ],
            "Витамины и минералы": [
                "Мультивитамины для спортсменов",
                "Омега-3",
                "Витамин D3",
                "Магний и цинк"
            ],
            "Аминокислоты": [
                "BCAA 2:1:1",
                "Глютамин",
                "Аргинин",
                "Бета-аланин"
            ],
        }

        categories = []
        for name in category_data.keys():
            if not name.strip():
                continue
            slug = generate_unique_slug_for_category(name)
            category = Category.objects.create(name=name, slug=slug)
            categories.append(category)
        self.stdout.write("✅ Категории созданы.")

        # --- Продукты ---
        products = []
        for category in categories:
            for product_name in category_data[category.name]:
                product = Product.objects.create(
                    name=product_name,
                    description=fake.paragraph(nb_sentences=3),
                    price=random.randint(700, 8000),
                    stock=random.randint(10, 100),
                    category=category,
                )
                products.append(product)
        self.stdout.write("✅ Продукты созданы.")

        # --- Избранное ---
        for user in users:
            for product in random.sample(products, 3):
                Favorite.objects.get_or_create(user=user, product=product)
        self.stdout.write("✅ Избранные товары добавлены.")

        # --- Отзывы ---
        for product in products:
            for user in random.sample(users, 2):
                Review.objects.create(
                    user=user,
                    product=product,
                    rating=random.randint(3, 5),
                    text=random.choice([
                        "Отличный продукт, беру не первый раз!",
                        "Доволен качеством, эффект есть.",
                        "Средне, ожидал большего.",
                        "Хорошая цена и доставка быстрая."
                    ])
                )
        self.stdout.write("✅ Отзывы созданы.")

        # --- Заказы ---
        for user in users:
            for _ in range(2):
                order = Order.objects.create(
                    user=user,
                    created_at=timezone.now(),
                    status=random.choice(["pending", "shipped", "delivered"]),
                    total_price=0
                )
                items = random.sample(products, 3)
                total = 0
                for product in items:
                    qty = random.randint(1, 3)
                    price = product.price
                    total += qty * price
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        buy_price=price
                    )
                order.total_price = total
                order.save()
        self.stdout.write("✅ Заказы созданы.")

        # --- Статьи ---
        articles = []
        article_titles = [
            "Как выбрать лучший протеин?",
            "5 способов ускорить восстановление после тренировки",
            "Роль креатина в росте мышц",
            "Правильное питание для набора массы",
            "Почему важен витамин D для спортсмена"
        ]
        for _ in range(5):
            title = random.choice(article_titles)
            slug = generate_unique_slug_for_article(title)
            article = Article.objects.create(
                author=random.choice(users),
                title=title,
                slug=slug,
                content=fake.paragraph(nb_sentences=6)
            )
            articles.append(article)
        self.stdout.write("✅ Статьи созданы.")

        # --- Комментарии ---
        for article in articles:
            for user in random.sample(users, 3):
                Comment.objects.create(
                    article=article,
                    user=user,
                    text=random.choice([
                        "Отличная статья, спасибо!",
                        "Теперь стало понятнее, как принимать добавки.",
                        "Полезно, возьму на заметку.",
                        "Автор, расскажи подробнее про дозировки!"
                    ])
                )
        self.stdout.write("✅ Комментарии созданы.")

        # --- Лайки ---
        likeable_models = [Article, Comment, Review]
        for user in users:
            for model in likeable_models:
                model_ct = ContentType.objects.get_for_model(model)
                objects = model.objects.all()
                for obj in random.sample(list(objects), min(3, len(objects))):
                    Like.objects.get_or_create(
                        user=user,
                        content_type=model_ct,
                        object_id=obj.id,
                        is_like=random.choice([True, False])
                    )
        self.stdout.write("✅ Лайки добавлены.")
        self.stdout.write(self.style.SUCCESS("🎉 База успешно заполнена данными!"))

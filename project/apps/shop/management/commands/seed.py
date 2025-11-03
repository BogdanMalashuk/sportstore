from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.shop.models import Category, Product, CartItem, Order, OrderItem, Like, Review
from apps.articles.models import Article, Comment
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from django.utils import timezone
from faker import Faker
import random

fake = Faker('ru_RU')


def unique_slug(model, field_value, default="item"):
    base_slug = slugify(field_value) or default
    slug = base_slug
    i = 1
    while model.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{i}"
        i += 1
    return slug


class Command(BaseCommand):
    help = "Заполняет базу тестовыми данными"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Начинаем заполнение базы...")

        Like.objects.all().delete()
        Comment.objects.all().delete()
        Review.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CartItem.objects.all().delete()

        Product.objects.all().delete()
        Category.objects.all().delete()
        Article.objects.all().delete()
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
        self.stdout.write("✅ Пользователи созданы.")

        category_names = [
            "Протеины",
            "Креатины",
            "Жиросжигатели",
            "Витамины и минералы",
            "Аминокислоты"
        ]
        categories = []
        for name in category_names:
            category = Category.objects.create(
                name=name,
                slug=unique_slug(Category, name)
            )
            categories.append(category)
        self.stdout.write("✅ Категории созданы.")

        # --- Продукты ---
        products = []
        for category in categories:
            for _ in range(4):
                product_name = f"{fake.word().capitalize()} {category.name[:-1]}"
                product = Product.objects.create(
                    name=product_name,
                    description=fake.paragraph(nb_sentences=3),
                    price=random.randint(700, 8000),
                    stock=random.randint(10, 100),
                    category=category,
                )
                products.append(product)
        self.stdout.write("✅ Продукты созданы.")

        # --- CartItem ---
        for user in users:
            for product in random.sample(products, 3):
                CartItem.objects.create(
                    user=user,
                    product=product,
                    quantity=random.randint(1, 3)
                )
        self.stdout.write("✅ Корзины пользователей созданы.")

        # --- Заказы ---
        for user in users:
            for _ in range(2):
                order = Order.objects.create(
                    user=user,
                    status=random.choice(["pending", "shipped", "delivered"]),
                    total_price=0,
                    created_at=timezone.now()
                )
                total = 0
                for product in random.sample(products, 3):
                    qty = random.randint(1, 3)
                    total += qty * product.price
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        buy_price=product.price
                    )
                order.total_price = total
                order.save()
        self.stdout.write("✅ Заказы созданы.")

        # --- Отзывы ---
        for product in products:
            for user in random.sample(users, 2):
                Review.objects.create(
                    user=user,
                    product=product,
                    rating=random.randint(3, 5),
                    text=fake.sentence()
                )
        self.stdout.write("✅ Отзывы созданы.")

        # --- Статьи ---
        articles = []
        for _ in range(5):
            title = fake.sentence(nb_words=5)
            article = Article.objects.create(
                title=title,
                slug=unique_slug(Article, title),
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
                    text=fake.sentence()
                )
        self.stdout.write("✅ Комментарии созданы.")

        # --- Лайки ---
        likeable_models = [Article, Comment, Review]
        for user in users:
            for model in likeable_models:
                ct = ContentType.objects.get_for_model(model)
                for obj in random.sample(list(model.objects.all()), min(3, model.objects.count())):
                    Like.objects.create(
                        user=user,
                        content_type=ct,
                        object_id=obj.id,
                        is_like=random.choice([True, False])
                    )
        self.stdout.write("✅ Лайки добавлены.")
        self.stdout.write(self.style.SUCCESS("🎉 База успешно заполнена!"))

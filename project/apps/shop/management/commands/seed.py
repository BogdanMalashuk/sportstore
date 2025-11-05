from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.shop.models import Category, Product, CartItem, Order, OrderItem, Like, Review
from apps.articles.models import Article, Comment
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from django.utils import timezone
import random


def unique_slug(model, field_value, default="item"):
    base_slug = slugify(field_value) or default
    slug = base_slug
    i = 1
    while model.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{i}"
        i += 1
    return slug


class Command(BaseCommand):
    help = "Заполняет базу осмысленными тестовыми данными"

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

        # --- Категории ---
        category_data = [
            ("Протеины", "Белковые добавки для набора мышечной массы и восстановления."),
            ("Креатины", "Добавки для увеличения силы, выносливости и продуктивности тренировок."),
            ("Жиросжигатели", "Препараты, способствующие ускорению обмена веществ и снижению жировой массы."),
            ("Витамины и минералы", "Необходимые микроэлементы для здоровья и поддержки организма при нагрузках."),
            ("Аминокислоты", "BCAA и другие аминокислоты для восстановления и роста мышц."),
        ]

        categories = []
        for name, desc in category_data:
            category = Category.objects.create(
                name=name,
                slug=unique_slug(Category, name),
                description=desc
            )
            categories.append(category)
        self.stdout.write("✅ Категории созданы.")

        # --- Продукты ---
        product_data = {
            "Протеины": [
                ("Optimum Nutrition Gold Standard Whey", "Самый популярный сывороточный протеин в мире. Отлично усваивается, поддерживает рост мышц."),
                ("Dymatize ISO100", "Изолят с быстрым усвоением, подходит для приёма сразу после тренировки."),
                ("Mutant Whey", "Высококалорийный протеин для быстрого набора массы."),
                ("Syntha-6", "Протеиновая смесь с отличным вкусом и длительным высвобождением аминокислот.")
            ],
            "Креатины": [
                ("MyProtein Creatine Monohydrate", "Креатин моногидрат для повышения силы и выносливости."),
                ("Optimum Nutrition Micronized Creatine", "Микронизированный креатин для лучшего усвоения."),
                ("Cell-Tech Hardcore", "Комплекс с креатином и углеводами для взрывного роста силы."),
                ("Universal Creatine", "Классический креатин с отличным соотношением цена/качество.")
            ],
            "Жиросжигатели": [
                ("Lipo-6 Black", "Мощный термогеник для ускорения метаболизма."),
                ("Hydroxycut Hardcore Elite", "Формула для контроля аппетита и повышения энергии."),
                ("Animal Cuts", "Многокомпонентный жиросжигатель для сушки тела."),
                ("Black Spider 25", "Интенсивная формула для продвинутых пользователей.")
            ],
            "Витамины и минералы": [
                ("Opti-Men", "Мультивитамины для активных мужчин."),
                ("Animal Pak", "Полный комплекс витаминов и минералов для спортсменов."),
                ("Daily Formula", "Базовый витаминный комплекс для ежедневного применения."),
                ("NOW Vitamin D3 5000 IU", "Поддержка иммунитета и костей, особенно в зимний период.")
            ],
            "Аминокислоты": [
                ("Scivation Xtend BCAA", "Aминокислоты с электролитами для восстановления."),
                ("BSN Amino X", "Энергетический аминокислотный комплекс."),
                ("Mutant BCAA 9.7", "Комплекс аминокислот для защиты мышц."),
                ("Optimum BCAA 5000 Powder", "Классическая формула BCAA для роста мышц.")
            ]
        }

        products = []
        for category in categories:
            for name, desc in product_data[category.name]:
                product = Product.objects.create(
                    name=name,
                    description=desc,
                    price=random.randint(1000, 6000),
                    category=category,
                )
                products.append(product)
        self.stdout.write("✅ Продукты созданы.")

        # --- Корзины ---
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
        review_texts = [
            "Отличный продукт, реально работает!",
            "Хорошее соотношение цена/качество.",
            "Уже месяц принимаю, результат есть.",
            "Вкус классный, хорошо растворяется.",
            "Не первый раз беру, рекомендую!"
        ]

        for product in products:
            for user in random.sample(users, 2):
                Review.objects.create(
                    user=user,
                    product=product,
                    rating=random.randint(4, 5),
                    text=random.choice(review_texts)
                )
        self.stdout.write("✅ Отзывы созданы.")

        # --- Статьи ---
        articles_data = [
            ("Как выбрать протеин для набора массы", "Подробное руководство о видах протеина, отличиях сывороточного и казеинового белка, и как подобрать под цели."),
            ("5 ошибок при приёме креатина", "Разбираем распространённые заблуждения и даём советы, как извлечь максимум из добавки."),
            ("Лучшие жиросжигатели 2025 года", "Обзор наиболее эффективных препаратов для снижения веса и повышения энергии."),
            ("Почему важны витамины для спортсмена", "Как микронутриенты влияют на восстановление, иммунитет и рост мышц."),
            ("Роль аминокислот в восстановлении", "Почему BCAA и EAA — обязательная часть спортивного рациона.")
        ]

        articles = []
        for title, content in articles_data:
            article = Article.objects.create(
                title=title,
                slug=unique_slug(Article, title),
                content=content
            )
            articles.append(article)
        self.stdout.write("✅ Статьи созданы.")

        # --- Комментарии ---
        comments_data = [
            "Полезная статья, многое прояснила.",
            "Спасибо! Теперь понимаю, какой протеин мне нужен.",
            "Интересная информация, особенно про дозировки.",
            "Согласен, креатин действительно помогает!",
            "Отличный разбор темы, жду новых материалов."
        ]

        for article in articles:
            for user in random.sample(users, 3):
                Comment.objects.create(
                    article=article,
                    user=user,
                    text=random.choice(comments_data)
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
        self.stdout.write(self.style.SUCCESS("🎉 База успешно заполнена осмысленными данными!"))

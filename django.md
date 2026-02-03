# Темы и вопросы для middle Django/DRF разработчика

## **Django Core**

### Архитектура и основы
- Понимание MTV паттерна (Model-Template-View)
- Жизненный цикл запроса в Django (от URL до ответа)
- Настройка settings.py: INSTALLED_APPS, MIDDLEWARE, DATABASE, STATIC/MEDIA
- Структура Django проекта vs приложения
- Django приложения: создание, регистрация, переиспользование
- Команды manage.py и создание собственных команд

### Модели и ORM
- Типы полей и их параметры (CharField, ForeignKey, ManyToMany и т.д.)
- Отношения: OneToOne, ForeignKey, ManyToMany, их различия и применение
- Meta класс: ordering, indexes, constraints, unique_together, permissions
- Менеджеры (Manager) и QuerySet: создание кастомных менеджеров
- Query оптимизация: select_related() vs prefetch_related()
- Понимание N+1 проблемы и способы её решения
- Агрегация и аннотация: aggregate(), annotate(), Count, Sum, Avg
- F() и Q() объекты для сложных запросов
- Транзакции: atomic(), select_for_update()
- Сигналы: pre_save, post_save, pre_delete, post_delete, их плюсы и минусы
- Миграции: создание, применение, откат, зависимости, RunPython, RunSQL
- Индексы базы данных и их влияние на производительность

### Views и URL
- Function-based views (FBV) vs Class-based views (CBV)
- Generic views: ListView, DetailView, CreateView, UpdateView, DeleteView
- Mixins: LoginRequiredMixin, UserPassesTestMixin и создание собственных
- URL routing: path(), re_path(), include(), именованные URL
- Reverse и reverse_lazy
- Обработка GET/POST запросов
- HttpRequest и HttpResponse объекты

### Формы
- Forms vs ModelForms
- Валидация: clean(), clean_<fieldname>(), валидаторы
- Widgets: кастомизация отображения полей
- Formsets и ModelFormsets
- Inline formsets для связанных моделей

### Аутентификация и авторизация
- User модель: AbstractUser vs AbstractBaseUser
- Система permissions и groups
- Декораторы: @login_required, @permission_required, @user_passes_test
- Кастомная аутентификация (бэкенды)
- Middleware для аутентификации

### Middleware
- Порядок выполнения middleware
- Создание собственного middleware
- process_request, process_response, process_exception

### Шаблоны (Templates)
- Template language: теги, фильтры, наследование
- Context processors
- Статические файлы и медиа файлы
- Кэширование шаблонов

### Кэширование
- Типы кэширования: per-site, per-view, template fragment, low-level
- Backend'ы: Redis, Memcached, database, filesystem
- Декораторы: @cache_page
- cache.get(), cache.set(), cache.delete()

### Тестирование
- TestCase vs TransactionTestCase
- setUp() и tearDown()
- Client для тестирования views
- Фикстуры
- Coverage и pytest-django

### Безопасность
- CSRF защита
- XSS защита
- SQL injection и как ORM защищает
- Clickjacking защита
- HTTPS и secure cookies
- Настройки безопасности: ALLOWED_HOSTS, SECRET_KEY, DEBUG

## **Django REST Framework**

### Основы DRF
- Serializers vs ModelSerializers
- Поля сериализаторов: типы, параметры (read_only, write_only, required)
- Вложенные сериализаторы и SerializerMethodField
- Валидация в сериализаторах: validate(), validate_<field>()
- to_representation() и to_internal_value()
- create() и update() методы

### Views и ViewSets
- APIView vs GenericAPIView
- Generic views: ListAPIView, RetrieveAPIView, CreateAPIView и т.д.
- ViewSet vs ModelViewSet vs ReadOnlyModelViewSet
- @action декоратор для кастомных эндпоинтов
- get_queryset() и get_object() переопределение

### Роутинг
- DefaultRouter vs SimpleRouter
- Автоматическая генерация URL из ViewSet
- Кастомные маршруты

### Аутентификация
- TokenAuthentication
- SessionAuthentication
- JWT (JSON Web Token) аутентификация
- BasicAuthentication
- Кастомная аутентификация
- Различия между authentication и permission

### Permissions
- IsAuthenticated, IsAdminUser, AllowAny
- IsAuthenticatedOrReadOnly
- DjangoModelPermissions
- Создание кастомных permissions
- has_permission() vs has_object_permission()

### Throttling
- AnonRateThrottle, UserRateThrottle
- Кастомный throttling
- Настройка rate limits

### Pagination
- PageNumberPagination
- LimitOffsetPagination
- CursorPagination
- Кастомная пагинация

### Фильтрация и поиск
- django-filter интеграция
- SearchFilter и OrderingFilter
- Кастомные фильтры
- filterset_fields vs filterset_class

### Версионирование API
- URLPathVersioning
- NamespaceVersioning
- AcceptHeaderVersioning
- QueryParameterVersioning

### Рендереры и парсеры
- JSONRenderer, BrowsableAPIRenderer
- JSONParser, FormParser, MultiPartParser
- Кастомные рендереры для специфичных форматов

### Обработка ошибок
- exception_handler
- Кастомные exception классы
- Правильные HTTP статус коды

### Документация API
- drf-spectacular или drf-yasg
- OpenAPI/Swagger спецификация
- Аннотации для документации

## **Продвинутые темы**

### Performance и оптимизация
- Database connection pooling
- Оптимизация запросов: explain, EXPLAIN ANALYZE
- only() и defer()
- Bulk operations: bulk_create(), bulk_update()
- Raw SQL когда необходимо
- Database indexes стратегии
- Кэширование на разных уровнях

### Celery и асинхронные задачи
- Настройка Celery с Django
- Создание задач: @task, @shared_task
- Periodic tasks (beat)
- Очереди и routing
- Monitoring: Flower

### WebSockets
- Django Channels
- ASGI vs WSGI
- Consumers и routing
- Channel layers (Redis)

### Docker и deployment
- Dockerfile для Django
- docker-compose.yml: Django, PostgreSQL, Redis, Nginx
- Gunicorn vs uWSGI
- Статические файлы на production
- Environment variables и секреты

### CI/CD
- Автоматическое тестирование
- Линтеры: flake8, black, isort
- Pre-commit hooks
- GitHub Actions / GitLab CI

### База данных
- PostgreSQL специфичные фичи
- Миграции в продакшене без даунтайма
- Database transactions и isolation levels
- Репликация и read replicas

### Архитектурные паттерны
- Repository pattern
- Service layer
- SOLID принципы в Django
- Разделение на модули и приложения

## **Практические вопросы на собеседованиях**

**Задачи на код:**
- Написать API для CRUD операций с оптимизацией запросов
- Реализовать кастомный permission класс
- Решить N+1 проблему в существующем коде
- Написать middleware для логирования запросов
- Реализовать soft delete для моделей
- Создать кастомный валидатор

**Ситуационные вопросы:**
- Как бы вы оптимизировали медленный эндпоинт?
- Как обеспечить безопасность API?
- Как организовать структуру большого проекта?
- Как реализовать многопользовательскую систему с разными ролями?
- Как обрабатывать файлы большого размера?
- Стратегия версионирования API при breaking changes

**SQL и база данных:**
- Написать raw SQL запрос и его ORM эквивалент
- Объяснить EXPLAIN результаты запроса
- Когда использовать индексы

Этот список покрывает основные темы для middle уровня. Рекомендую пройтись по каждой теме, попрактиковаться в написании кода и убедиться, что можете объяснить концепции своими словами.

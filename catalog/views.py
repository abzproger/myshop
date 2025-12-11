from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from .models import Category, ProductVariant, Product, AttributeValue, ContactMessage
from .forms import ContactForm


def index(request):
    """Главная страница интернет-магазина"""
    # Категории для главной страницы (почти статичные) — кэшируем на 1 час
    categories = cache.get('index_categories')
    if categories is None:
        categories = list(
            Category.objects.filter(parent__isnull=True)[:8]
        )
        cache.set('index_categories', categories, 60 * 60)

    # Популярные товары (активные варианты с изображениями) — кэшируем результат
    # сортировки по просмотрам на 5 минут.
    featured_products = cache.get('index_featured_products')
    if featured_products is None:
        variants_qs = ProductVariant.objects.filter(
            is_active=True,
            product__is_active=True
        ).select_related('product', 'product__category').prefetch_related('images')

        variants = list(variants_qs)  # Можно ограничить, если товаров станет очень много

        def get_views(v):
            key = f"product_variant:{v.id}:views"
            return cache.get(key, 0) or 0

        variants_sorted = sorted(variants, key=get_views, reverse=True)
        featured_products = variants_sorted[:12]
        cache.set('index_featured_products', featured_products, 5 * 60)
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
    }

    return render(request, 'catalog/index.html', context)


@cache_page(60 * 60)  # Страница полностью статичная — кэшируем целиком на 1 час
def about(request):
    """Страница 'О нас'"""
    return render(request, 'catalog/about.html')


def contacts(request):
    """Страница 'Контакты'"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact: ContactMessage = form.save(commit=False)
            contact.source_url = request.META.get('HTTP_REFERER', '')
            contact.save()

            # Пытаемся отправить письмо на почту магазина.
            subject_display = contact.get_subject_display() or "Обращение с формы контактов"
            email_subject = f"[Контакты MEBELHUB] {subject_display}"
            email_body = (
                f"Имя: {contact.name}\n"
                f"Email: {contact.email}\n"
                f"Телефон: {contact.phone}\n"
                f"Тема: {subject_display}\n\n"
                f"Сообщение:\n{contact.message}\n\n"
                f"Источник: {contact.source_url}"
            )

            to_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "info@mebelhub.ru"
            try:
                send_mail(
                    email_subject,
                    email_body,
                    to_email,
                    [to_email],
                    fail_silently=True,
                )
            except Exception:
                # Не падаем, даже если почта не настроена.
                pass

            messages.success(request, "Ваше сообщение успешно отправлено. Мы свяжемся с вами в ближайшее время.")
            return redirect('catalog:contacts')
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = ContactForm()

    return render(request, 'catalog/contacts.html', {'form': form})


def catalog(request, category_slug=None):
    """Страница каталога товаров"""
    # Получаем все категории для фильтра (почти статичные) — кэшируем на 1 час
    categories = cache.get('catalog_root_categories')
    if categories is None:
        categories = list(Category.objects.filter(parent__isnull=True))
        cache.set('catalog_root_categories', categories, 60 * 60)
    
    # Получаем товары (варианты)
    variants = ProductVariant.objects.filter(
        is_active=True,
        product__is_active=True
    ).select_related('product', 'product__category').prefetch_related('images')
    
    # Фильтрация по категории
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        # Находим все дочерние категории (многоуровнево), чтобы показывать товары
        # как из выбранной категории, так и из её подкатегорий.
        category_ids = [selected_category.id]
        frontier = [selected_category.id]
        while frontier:
            children = list(
                Category.objects.filter(parent_id__in=frontier).values_list("id", flat=True)
            )
            if not children:
                break
            category_ids.extend(children)
            frontier = children

        variants = variants.filter(product__category_id__in=category_ids)
    
    # Поиск
    search_query = request.GET.get('search', '')
    if search_query:
        variants = variants.filter(
            Q(product__name__icontains=search_query) |
            Q(product__description__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    # Сортировка
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_asc':
        # Сначала по цене варианта, потом по цене товара
        from django.db.models import F, Case, When
        from django.db.models.functions import Coalesce
        variants = variants.annotate(
            final_price=Coalesce('price', 'product__price')
        ).order_by('final_price', 'product__name')
    elif sort_by == 'price_desc':
        from django.db.models.functions import Coalesce
        variants = variants.annotate(
            final_price=Coalesce('price', 'product__price')
        ).order_by('-final_price', 'product__name')
    elif sort_by == 'name':
        variants = variants.order_by('product__name', 'name')
    else:
        variants = variants.order_by('product__name', 'name')
    
    # Подсчет товаров
    total_count = variants.count()
    
    context = {
        'categories': categories,
        'variants': variants,
        'selected_category': selected_category,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_count': total_count,
    }
    
    return render(request, 'catalog/catalog.html', context)


def product_detail(request, product_slug):
    """Детальная страница товара.

    При наличии параметра ?variant=<id> делает этот вариант основным:
    отображает его цену, характеристики и первое изображение.
    """
    # Получаем товар
    product = get_object_or_404(Product, slug=product_slug, is_active=True)

    # Получаем все активные варианты товара
    variants = product.variants.filter(is_active=True).prefetch_related('images', 'attributes')

    # Определяем выбранный вариант (из query-параметра или первый по умолчанию)
    selected_variant = None
    variant_id = request.GET.get('variant')
    if variants.exists():
        if variant_id:
            selected_variant = variants.filter(pk=variant_id).first()
        if selected_variant is None:
            selected_variant = variants.first()

    # Увеличиваем счётчик просмотров выбранного варианта в Redis
    if selected_variant:
        key = f"product_variant:{selected_variant.id}:views"
        try:
            cache.incr(key)
        except ValueError:
            # Если ключ ещё не существует или не число
            cache.set(key, 1)

    # Изображения ТОЛЬКО выбранного варианта
    variant_images = []
    main_image = None
    if selected_variant:
        variant_images = list(selected_variant.images.all())
        if variant_images:
            main_image = variant_images[0]

    # Характеристики выбранного варианта
    attributes = None
    if selected_variant:
        attributes = AttributeValue.objects.filter(
            variant=selected_variant
        ).select_related('attribute')

    # Похожие товары (из той же категории)
    related_products = ProductVariant.objects.filter(
        product__category=product.category,
        product__is_active=True,
        is_active=True
    ).exclude(product=product).select_related('product').prefetch_related('images')[:4]

    context = {
        'product': product,
        'variants': variants,
        'selected_variant': selected_variant,
        'variant_images': variant_images,
        'main_image': main_image,
        'attributes': attributes,
        'related_products': related_products,
    }

    return render(request, 'catalog/product_detail.html', context)

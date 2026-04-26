import json
import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import Truncator
from .models import Category, ProductVariant, Product, AttributeValue, ContactMessage
from .forms import ContactForm


def _absolute_url(path):
    if not path:
        return ""
    if str(path).startswith(("http://", "https://")):
        return str(path)
    return f"{settings.SITE_URL.rstrip('/')}{path}"


def _meta_description(text, fallback):
    clean_text = strip_tags(text or "").replace("\n", " ").strip()
    if not clean_text:
        clean_text = fallback
    return Truncator(clean_text).chars(155)


def index(request):
    """Главная страница интернет-магазина"""
    # Категории для главной страницы (почти статичные) — кэшируем на 1 час
    categories = cache.get('index_categories')
    if categories is None:
        categories = list(
            Category.objects.filter(parent__isnull=True)[:8]
        )
        cache.set('index_categories', categories, 60 * 60)

    # Популярные товары (активные варианты) — кэшируем результат
    # сортировки по просмотрам на 5 минут.
    featured_limit = 4
    featured_cache_key = f"index_featured_products:{featured_limit}"
    featured_products = cache.get(featured_cache_key)
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
        featured_products = variants_sorted[:featured_limit]
        cache.set(featured_cache_key, featured_products, 5 * 60)

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'meta_description': settings.SITE_DESCRIPTION,
        'og_title': "SofaArt — интернет-магазин мебели",
        'canonical_url': _absolute_url(reverse('catalog:index')),
    }

    return render(request, 'catalog/index.html', context)


@cache_page(60 * 60)  # Страница полностью статичная — кэшируем целиком на 1 час
def about(request):
    """Страница 'О нас'"""
    return render(request, 'catalog/about.html')


@cache_page(60 * 60)  # Страница полностью статичная — кэшируем целиком на 1 час
def privacy(request):
    """Страница Политики конфиденциальности"""
    return render(request, 'catalog/privacy.html')


def contacts(request):
    """Страница 'Контакты'"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact: ContactMessage = form.save(commit=False)
            contact.source_url = (request.META.get('HTTP_REFERER', '') or '')[:500]
            contact.save()

            # Пытаемся отправить письмо на почту магазина.
            subject_display = contact.get_subject_display() or "Обращение с формы контактов"
            email_subject = f"[Контакты SofaArt] {subject_display}"
            email_body = (
                f"Имя: {contact.name}\n"
                f"Email: {contact.email}\n"
                f"Телефон: {contact.phone}\n"
                f"Тема: {subject_display}\n\n"
                f"Сообщение:\n{contact.message}\n\n"
                f"Источник: {contact.source_url}"
            )

            to_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "info@sofaart.ru"
            try:
                send_mail(
                    email_subject,
                    email_body,
                    to_email,
                    [to_email],
                    fail_silently=False,
                )
            except Exception as e:
                logging.getLogger(__name__).exception("Ошибка отправки письма с формы контактов: %s", e)

            messages.success(request, "Ваше сообщение успешно отправлено. Мы свяжемся с вами в ближайшее время.")
            return redirect('catalog:contacts')
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = ContactForm()

    return render(request, 'catalog/contacts.html', {'form': form})


def catalog(request, category_slug=None):
    """Страница каталога товаров"""
    # Поддержка фильтра категории через querystring:
    # /catalog/?category=<slug>
    # (исторически формы на странице могли отправлять category в GET).
    category_slug_from_get = False
    if not category_slug:
        category_slug = (request.GET.get("category") or "").strip() or None
        category_slug_from_get = bool(category_slug)
    else:
        # Канонизация URL: если категория уже задана в пути (/catalog/<slug>/),
        # параметр ?category=<slug> из querystring избыточен и может приводить
        # к "плавающему" поведению при разных вариантах формирования ссылок.
        if "category" in request.GET:
            qs = request.GET.copy()
            qs.pop("category", None)
            querystring = qs.urlencode()
            return redirect(f"{request.path}?{querystring}" if querystring else request.path)

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
        # Если категория пришла из querystring и slug невалидный —
        # не падаем 404, а считаем, что фильтра по категории нет.
        if category_slug_from_get:
            selected_category = Category.objects.filter(slug=category_slug).first()
            if not selected_category:
                category_slug = None

        if category_slug and selected_category is None:
            selected_category = get_object_or_404(Category, slug=category_slug)

    if selected_category:
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
        variants = variants.annotate(
            final_price=Coalesce('price', 'product__price')
        ).order_by('final_price', 'product__name')
    elif sort_by == 'price_desc':
        variants = variants.annotate(
            final_price=Coalesce('price', 'product__price')
        ).order_by('-final_price', 'product__name')
    elif sort_by == 'name':
        variants = variants.order_by('product__name', 'name')
    else:
        variants = variants.order_by('product__name', 'name')
    
    # Подсчет товаров
    total_count = variants.count()

    # Пагинация
    per_page = 12
    try:
        per_page = int(request.GET.get("per_page", per_page))
    except (TypeError, ValueError):
        per_page = 12
    # Простая защита от слишком больших значений (чтобы не уронить страницу)
    per_page = max(1, min(per_page, 48))

    paginator = Paginator(variants, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Чтобы ссылки пагинации сохраняли текущие фильтры/поиск/сортировку
    qs = request.GET.copy()
    qs.pop("page", None)
    # Если категория в пути — не тащим её дубль в querystring
    if category_slug and not category_slug_from_get:
        qs.pop("category", None)
    querystring = qs.urlencode()
    
    meta_description = (
        "Каталог мебели SofaArt: стулья, мягкая мебель и товары для дома "
        "с доставкой по России."
    )
    if selected_category:
        meta_description = _meta_description(
            selected_category.description,
            f"{selected_category.name} в интернет-магазине SofaArt с доставкой по России.",
        )

    query_keys = set(request.GET.keys())
    meta_robots = "noindex, follow" if query_keys else "index, follow"
    canonical_url = _absolute_url(request.path)

    context = {
        'categories': categories,
        'variants': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'querystring': querystring,
        'selected_category': selected_category,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_count': total_count,
        'meta_description': meta_description,
        'meta_robots': meta_robots,
        'canonical_url': canonical_url,
        'og_title': (
            f"{selected_category.name} - SofaArt"
            if selected_category
            else "Каталог мебели - SofaArt"
        ),
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

    canonical_url = _absolute_url(reverse('catalog:product_detail', kwargs={'product_slug': product.slug}))
    meta_description = _meta_description(
        product.description,
        f"Купить {product.name} в интернет-магазине SofaArt с доставкой по России.",
    )
    og_image = _absolute_url(main_image.image.url) if main_image else ""

    product_json_ld = None
    if selected_variant:
        offer_price = selected_variant.get_price_with_discount()
        product_schema = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Product",
                    "@id": f"{canonical_url}#product",
                    "name": product.name,
                    "description": meta_description,
                    "sku": selected_variant.sku,
                    "category": product.category.name,
                    "image": [og_image] if og_image else [],
                    "brand": {
                        "@type": "Brand",
                        "name": "SofaArt",
                    },
                    "offers": {
                        "@type": "Offer",
                        "url": canonical_url,
                        "priceCurrency": "RUB",
                        "price": format(offer_price, "f"),
                        "availability": (
                            "https://schema.org/InStock"
                            if selected_variant.stock > 0
                            else "https://schema.org/OutOfStock"
                        ),
                        "itemCondition": "https://schema.org/NewCondition",
                    },
                },
                {
                    "@type": "BreadcrumbList",
                    "@id": f"{canonical_url}#breadcrumbs",
                    "itemListElement": [
                        {
                            "@type": "ListItem",
                            "position": 1,
                            "name": "Главная",
                            "item": _absolute_url(reverse('catalog:index')),
                        },
                        {
                            "@type": "ListItem",
                            "position": 2,
                            "name": "Каталог",
                            "item": _absolute_url(reverse('catalog:catalog')),
                        },
                        {
                            "@type": "ListItem",
                            "position": 3,
                            "name": product.category.name,
                            "item": _absolute_url(
                                reverse(
                                    'catalog:catalog_by_category',
                                    kwargs={'category_slug': product.category.slug},
                                )
                            ),
                        },
                        {
                            "@type": "ListItem",
                            "position": 4,
                            "name": product.name,
                            "item": canonical_url,
                        },
                    ],
                },
            ],
        }
        product_json_ld = json.dumps(product_schema, ensure_ascii=False)

    context = {
        'product': product,
        'variants': variants,
        'selected_variant': selected_variant,
        'variant_images': variant_images,
        'main_image': main_image,
        'attributes': attributes,
        'related_products': related_products,
        'meta_description': meta_description,
        'canonical_url': canonical_url,
        'og_title': f"{product.name} - SofaArt",
        'og_image': og_image,
        'product_json_ld': product_json_ld,
    }

    return render(request, 'catalog/product_detail.html', context)

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Category, ProductVariant, Product, AttributeValue


def index(request):
    """Главная страница интернет-магазина"""
    # Получаем категории (первые 8, без родительских для главной страницы)
    categories = Category.objects.filter(parent__isnull=True)[:8]
    
    # Получаем популярные товары (активные варианты с изображениями)
    featured_products = ProductVariant.objects.filter(
        is_active=True,
        product__is_active=True
    ).select_related('product', 'product__category').prefetch_related('images')[:12]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
    }
    
    return render(request, 'catalog/index.html', context)


def about(request):
    """Страница 'О нас'"""
    return render(request, 'catalog/about.html')


def contacts(request):
    """Страница 'Контакты'"""
    return render(request, 'catalog/contacts.html')


def catalog(request, category_slug=None):
    """Страница каталога товаров"""
    # Получаем все категории для фильтра
    categories = Category.objects.filter(parent__isnull=True)
    
    # Получаем товары (варианты)
    variants = ProductVariant.objects.filter(
        is_active=True,
        product__is_active=True
    ).select_related('product', 'product__category').prefetch_related('images')
    
    # Фильтрация по категории
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        variants = variants.filter(product__category=selected_category)
    
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

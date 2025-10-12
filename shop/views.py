# shop/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from .models import Product, Participant
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from .utils.embeddings import OpenAIEmbeddingGenerator
from datetime import datetime, timedelta
import random

def consent_form(request):
    """
    실험 동의서 페이지
    """
    if request.method == 'POST':
        # 동의 체크박스가 모두 선택되었는지 확인
        consent_research = request.POST.get('consent_research')
        consent_data = request.POST.get('consent_data')
        consent_participation = request.POST.get('consent_participation')
        name = request.POST.get('name', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        if consent_research and consent_data and consent_participation and name and student_id and phone:
            # 참여자 저장
            ip = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR')
            if ip and ',' in ip:
                ip = ip.split(',')[0].strip()
            participant = Participant.objects.create(
                name=name,
                student_id=student_id,
                phone=phone,
                consent_research=True,
                consent_data=True,
                consent_participation=True,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=ip or None,
            )
            # 세션에 동의 상태 및 참여자 ID 저장
            request.session['experiment_consent'] = True
            request.session['participant_id'] = participant.id
            return redirect('home')
        else:
            return render(request, 'shop/consent_form.html', {
                'error': '모든 동의 항목과 기본 정보를 정확히 입력해주세요.'
            })
    
    return render(request, 'shop/consent_form.html')

@ensure_csrf_cookie
def home(request):
    """쿠팡 메인 느낌의 랜딩 페이지: 상단 배너, 카테고리, 오늘의 발견, 실시간 검색어 등"""
    # 실험 동의 확인
    if not request.session.get('experiment_consent', False):
        return redirect('consent_form')

    # 오늘의 발견: 제휴 상품 위주 상위 8개 랜덤
    qs = Product.objects.all()
    affiliated = list(qs.filter(if_affiliated=True)[:30])
    random.shuffle(affiliated)
    todays = affiliated[:8] if affiliated else list(qs[:8])

    # 인기 카테고리 샘플
    categories = (
        Product.objects.values_list('category', flat=True)
        .distinct()
    )
    categories = [c for c in categories if c][:10]

    context = {
        'todays': todays,
        'categories': categories,
    }
    return render(request, 'shop/home.html', context)

@ensure_csrf_cookie
def product_list(request):
    """
    전체 상품 목록을 보여주는 페이지
    """
    # 실험 동의 확인
    if not request.session.get('experiment_consent', False):
        return redirect('consent_form')
    
    q = request.GET.get('q', '').strip()
    products = Product.objects.all()
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(brand__icontains=q) | Q(category__icontains=q)
        )
    context = {'products': products, 'q': q}
    return render(request, 'shop/product_list.html', context)

@ensure_csrf_cookie
def product_detail(request, product_id):
    """
    상품 상세 페이지
    """
    # 실험 동의 확인
    if not request.session.get('experiment_consent', False):
        return redirect('consent_form')
    
    product = get_object_or_404(Product, id=product_id)
    
    # 리뷰 데이터 파싱
    reviews = []
    if product.reviews:
        try:
            reviews = json.loads(product.reviews)
        except json.JSONDecodeError:
            reviews = []
    
    # 관련 상품 추천 (같은 카테고리의 다른 상품들)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product_id)[:4]
    
    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
    }
    return render(request, 'shop/product_detail.html', context)

def cart_view(request):
    """
    장바구니 페이지. 여기에 조작된 추천 로직이 들어갑니다.
    """
    # 실험 동의 확인
    if not request.session.get('experiment_consent', False):
        return redirect('consent_form')
    
    # 세션 기반 장바구니: {product_id: quantity}
    cart = request.session.get('cart', {})
    cart_product_ids = list(map(int, cart.keys())) if cart else []
    cart_products = Product.objects.filter(id__in=cart_product_ids)
    
    # --- 💡 연구 핵심: 조작된 추천 로직 ---
    # 1. 장바구니 상품들의 카테고리를 가져옵니다.
    cart_categories = [p.category for p in cart_products]
    
    # 2. 제휴 브랜드(if_affiliated=True)이면서,
    #    장바구니 상품과 카테고리가 겹치는 상품들을 추천 후보로 선정합니다.
    recommended_products = Product.objects.filter(
        if_affiliated=True,
        category__in=cart_categories
    ).exclude(
        id__in=cart_product_ids # 장바구니에 이미 있는 상품은 제외
    ).distinct()[:5] # 추천 상품 5개만 선택
    
    # "당신의 취향을 기반으로 추천합니다" 라는 문구와 함께 전달
    context = {
        'cart_products': cart_products,
        'recommended_products': recommended_products,
        'cart_quantities': cart,
    }
    return render(request, 'shop/cart.html', context)


def add_to_cart(request):
    """AJAX: 장바구니 담기 (세션 기반)
    POST: product_id, quantity(옵션, 기본 1)
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')

    try:
        product_id = int(request.POST.get('product_id'))
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'invalid-params'}, status=400)

    # 존재 검증
    try:
        Product.objects.only('id').get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'product-not-found'}, status=404)

    cart = request.session.get('cart', {})
    current_qty = int(cart.get(str(product_id), 0))
    cart[str(product_id)] = current_qty + quantity
    request.session['cart'] = cart
    request.session.modified = True

    return JsonResponse({'ok': True, 'cart': cart})


def api_ai_recommendations(request):
    """AJAX: 장바구니 기반 AI 추천 (제휴 상품 한정)
    GET: limit(옵션, 기본 8)
    """
    if request.method != 'GET':
        return HttpResponseBadRequest('Invalid method')

    # 세션 장바구니
    cart = request.session.get('cart', {})
    cart_ids = [int(k) for k in cart.keys()] if cart else []
    if not cart_ids:
        return JsonResponse({'ok': True, 'results': []})

    try:
        limit = int(request.GET.get('limit', 8))
    except ValueError:
        limit = 8

    gen = OpenAIEmbeddingGenerator()
    results = gen.recommend_for_products(
        product_ids=cart_ids,
        limit=limit,
        affiliated_only=True,
        use_categories=True,
    )

    return JsonResponse({'ok': True, 'results': results})


def _suggest_from_products(query: str, limit: int = 8):
    """간단한 제품명/브랜드/카테고리 기반 자동완성 후보 생성"""
    if not query:
        return []
    base = Product.objects.filter(
        Q(name__icontains=query) | Q(brand__icontains=query) | Q(category__icontains=query)
    )
    names = list(base.values_list('name', flat=True)[:limit])
    brands = list(base.values_list('brand', flat=True)[:limit])
    cats = list(base.values_list('category', flat=True)[:limit])
    # 우선순위: 이름 > 브랜드 > 카테고리, 중복 제거
    seen, out = set(), []
    for s in names + brands + cats:
        if s and s not in seen:
            out.append(s)
            seen.add(s)
        if len(out) >= limit:
            break
    return out


@ensure_csrf_cookie
def api_search_suggest(request):
    if request.method != 'GET':
        return HttpResponseBadRequest('Invalid method')
    q = request.GET.get('q', '').strip()
    try:
        limit = int(request.GET.get('limit', 8))
    except ValueError:
        limit = 8
    return JsonResponse({'ok': True, 'suggestions': _suggest_from_products(q, limit)})


@ensure_csrf_cookie
def api_search_trending(request):
    """가상의 실시간 검색어 제공: 최근 인기 카테고리/브랜드/키워드 믹스"""
    if request.method != 'GET':
        return HttpResponseBadRequest('Invalid method')
    brands = list(Product.objects.values_list('brand', flat=True).distinct()[:30])
    cats = list(Product.objects.values_list('category', flat=True).distinct()[:30])
    picks = [b for b in brands if b][:10] + [c for c in cats if c][:10]
    random.shuffle(picks)
    trending = picks[:10]
    # 랭킹과 변동 화살표 가상 부여
    arrows = ['▲', '▼', '→']
    payload = [
        {'rank': i+1, 'term': t, 'delta': random.choice(arrows)}
        for i, t in enumerate(trending)
    ]
    return JsonResponse({'ok': True, 'trending': payload})
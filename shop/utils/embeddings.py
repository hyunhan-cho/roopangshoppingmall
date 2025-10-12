import os
import json
import numpy as np
from django.db import connection
from openai import OpenAI

class OpenAIEmbeddingGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "text-embedding-3-small"  # 1536차원, 저렴한 비용
    
    def get_embedding(self, text):
        """텍스트를 임베딩 벡터로 변환"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text.strip()
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"임베딩 생성 오류: {e}")
            return None
    
    def generate_product_embeddings(self, product):
        """상품 정보로부터 임베딩 생성"""
        # 상품명 + 브랜드 + 카테고리 조합
        name_text = f"{product.name} {product.brand} {product.category}"
        
        # 리뷰 요약 텍스트
        reviews = product.get_reviews_list()
        review_comments = [r.get('comment', '') for r in reviews[:5]]  # 상위 5개 리뷰
        review_text = " ".join(review_comments) if review_comments else name_text
        
        # 임베딩 생성
        name_embedding = self.get_embedding(name_text)
        description_embedding = self.get_embedding(review_text)
        
        return name_embedding, description_embedding
    
    def cosine_similarity(self, vec1, vec2):
        """코사인 유사도 계산"""
        if isinstance(vec1, str):
            vec1 = json.loads(vec1)
        if isinstance(vec2, str):
            vec2 = json.loads(vec2)
            
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def search_similar_products(self, query, limit=5, exclude_ids=None, affiliated_only=False, categories=None):
        """벡터 유사도 기반 상품 검색
        - affiliated_only: 제휴 상품만
        - categories: 카테고리 제한(list[str])
        """
        from shop.models import Product
        
        query_embedding = self.get_embedding(query)
        if not query_embedding:
            return []
        
        # PostgreSQL + pgvector 사용 여부 확인
        try:
            from pgvector.django import VectorField
            return self._search_with_pgvector(query_embedding, limit, exclude_ids, affiliated_only, categories)
        except ImportError:
            return self._search_with_python(query_embedding, limit, exclude_ids, affiliated_only, categories)
    
    def _search_with_pgvector(self, query_embedding, limit, exclude_ids, affiliated_only=False, categories=None):
        """PostgreSQL pgvector 확장 사용"""
        from shop.models import Product
        
        with connection.cursor() as cursor:
            where_clauses = ["name_embedding IS NOT NULL"]
            params = []
            
            if affiliated_only:
                where_clauses.append("if_affiliated = true")
            
            if categories:
                where_clauses.append(f"category = ANY(%s)")
                params.append(categories)
            
            if exclude_ids:
                where_clauses.append(f"id <> ALL(%s)")
                params.append(exclude_ids)
            
            where_sql = " AND ".join(where_clauses)
            
            # query_embedding 파라미터 2회 사용(정렬과 선택)
            params = [query_embedding] + params + [query_embedding, limit]
            
            cursor.execute(f"""
                SELECT id, name, brand, price, if_affiliated, img, category,
                       (name_embedding <-> %s::vector) as distance
                FROM shop_product 
                WHERE {where_sql}
                ORDER BY name_embedding <-> %s::vector
                LIMIT %s
            """, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'brand': row[2], 
                    'price': row[3],
                    'if_affiliated': row[4],
                    'img': row[5],
                    'category': row[6],
                    'similarity_score': max(0, 1 - row[7])  # 거리를 유사도로 변환
                })
            
            return results
    
    def _search_with_python(self, query_embedding, limit, exclude_ids, affiliated_only=False, categories=None):
        """Python 기반 유사도 검색 (SQLite 호환)"""
        from shop.models import Product
        
        products = Product.objects.exclude(name_embedding__isnull=True)
        if affiliated_only:
            products = products.filter(if_affiliated=True)
        if categories:
            products = products.filter(category__in=categories)
        if exclude_ids:
            products = products.exclude(id__in=exclude_ids)
        
        similarities = []
        for product in products:
            if product.name_embedding:
                similarity = self.cosine_similarity(query_embedding, product.name_embedding)
                similarities.append((product, similarity))
        
        # 유사도 순으로 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for product, similarity in similarities[:limit]:
            results.append({
                'id': product.id,
                'name': product.name,
                'brand': product.brand,
                'price': product.price,
                'if_affiliated': product.if_affiliated,
                'img': product.img,
                'category': product.category,
                'similarity_score': similarity
            })
        
        return results

    def recommend_for_products(self, product_ids, limit=8, affiliated_only=True, use_categories=True):
        """장바구니 상품들로부터 집합 임베딩을 구성해 유사 상품 추천.
        - 장바구니 상품은 제외, 기본적으로 제휴 상품만 대상으로 함.
        - 카테고리 제한 옵션(use_categories) 제공.
        """
        from shop.models import Product
        items = list(Product.objects.filter(id__in=product_ids))
        if not items:
            return []
        # 쿼리 텍스트: 이름/브랜드/카테고리 + 리뷰 요약 일부를 합침
        parts = []
        for p in items:
            parts.append(f"{p.name} {p.brand} {p.category}")
            try:
                revs = p.get_reviews_list()
                if revs:
                    snippets = " ".join([r.get('comment', '') for r in revs[:2]])
                    if snippets:
                        parts.append(snippets)
            except Exception:
                pass
        query_text = " | ".join(parts)
        cats = list({p.category for p in items}) if use_categories else None
        return self.search_similar_products(
            query=query_text,
            limit=limit,
            exclude_ids=product_ids,
            affiliated_only=affiliated_only,
            categories=cats,
        )
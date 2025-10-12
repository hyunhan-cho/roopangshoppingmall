# shop/models.py
from django.db import models
from django.utils import timezone
import json

# pgvector 사용 가능 여부 확인
try:
    from pgvector.django import VectorField
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False

class Product(models.Model):
    # product_id는 Django가 자동으로 생성하는 id 필드를 사용합니다.
    classification = models.CharField(max_length=100, default='생활용품')  # 상위 분류 (예: 생활용품)
    category = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    price = models.IntegerField()
    img = models.URLField(max_length=500) # 이미지 URL을 저장할 필드
    if_affiliated = models.BooleanField(default=False) # 제휴 브랜드 여부
    reviews = models.TextField(blank=True) # 리뷰 텍스트 (비어있을 수 있음)
    
    # OpenAI 임베딩 필드 (1536차원 - text-embedding-3-small)
    if VECTOR_AVAILABLE:
        name_embedding = VectorField(dimensions=1536, null=True, blank=True)
        description_embedding = VectorField(dimensions=1536, null=True, blank=True)
    else:
        # SQLite 호환용 (JSON 문자열로 저장)
        name_embedding = models.TextField(blank=True, null=True)
        description_embedding = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[{self.brand}] {self.name}"
    
    def get_reviews_list(self):
        """리뷰 JSON 데이터를 파싱해서 리스트로 반환"""
        if self.reviews:
            try:
                return json.loads(self.reviews)
            except json.JSONDecodeError:
                return []
        return []
    
    class Meta:
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['brand']),
            models.Index(fields=['if_affiliated']),
        ]


class Participant(models.Model):
    """연구 참여자 정보 및 동의 상태 기록"""
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=50)
    phone = models.CharField(max_length=30)

    consent_research = models.BooleanField(default=False)
    consent_data = models.BooleanField(default=False)
    consent_participation = models.BooleanField(default=False)

    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.student_id})"
from django.core.management.base import BaseCommand
from shop.models import Product
from shop.utils.embeddings import OpenAIEmbeddingGenerator
import json

class Command(BaseCommand):
    help = '모든 상품에 대해 OpenAI 임베딩을 생성합니다'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='기존 임베딩이 있어도 강제로 재생성합니다',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='배치 처리할 상품 개수 (기본값: 10)',
        )
        parser.add_argument(
            '--product-ids',
            nargs='+',
            type=int,
            help='특정 상품 ID들만 처리 (예: --product-ids 1 2 3)',
        )
    
    def handle(self, *args, **options):
        generator = OpenAIEmbeddingGenerator()
        
        # 처리할 상품들 선택
        if options['product_ids']:
            products = Product.objects.filter(id__in=options['product_ids'])
            self.stdout.write(f"지정된 상품 {len(products)}개 처리 중...")
        elif options['force']:
            products = Product.objects.all()
            self.stdout.write(f"모든 상품 {products.count()}개 강제 재생성 중...")
        else:
            # 임베딩이 없는 상품들만
            products = Product.objects.filter(
                name_embedding__isnull=True
            )
            self.stdout.write(f"임베딩이 없는 상품 {products.count()}개 처리 중...")
        
        if not products.exists():
            self.stdout.write(
                self.style.WARNING("처리할 상품이 없습니다.")
            )
            return
        
        total = products.count()
        processed = 0
        failed = 0
        batch_size = options['batch_size']
        
        # 배치 처리
        for i in range(0, total, batch_size):
            batch = products[i:i + batch_size]
            
            for product in batch:
                try:
                    self.stdout.write(f"[{processed + 1}/{total}] {product.name} 처리 중...")
                    
                    name_embedding, description_embedding = generator.generate_product_embeddings(product)
                    
                    if name_embedding and description_embedding:
                        # PostgreSQL의 경우 벡터로 저장, SQLite의 경우 JSON으로 저장
                        try:
                            # pgvector 사용 가능한지 확인
                            from pgvector.django import VectorField
                            product.name_embedding = name_embedding
                            product.description_embedding = description_embedding
                        except ImportError:
                            # SQLite의 경우 JSON 문자열로 저장
                            product.name_embedding = json.dumps(name_embedding)
                            product.description_embedding = json.dumps(description_embedding)
                        
                        product.save(update_fields=['name_embedding', 'description_embedding'])
                        processed += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ {product.name} 완료")
                        )
                    else:
                        failed += 1
                        self.stdout.write(
                            self.style.ERROR(f"✗ {product.name} 임베딩 생성 실패")
                        )
                        
                except Exception as e:
                    failed += 1
                    self.stdout.write(
                        self.style.ERROR(f"✗ {product.name} 오류: {e}")
                    )
            
            # 배치 완료 후 진행 상황 출력
            if i + batch_size < total:
                self.stdout.write(
                    self.style.WARNING(f"배치 완료: {min(i + batch_size, total)}/{total}")
                )
        
        # 최종 결과
        self.stdout.write("\n" + "="*50)
        self.stdout.write(
            self.style.SUCCESS(f"임베딩 생성 완료!")
        )
        self.stdout.write(f"성공: {processed}개")
        self.stdout.write(f"실패: {failed}개")
        self.stdout.write(f"총계: {processed + failed}개")
        
        if processed > 0:
            self.stdout.write(
                self.style.SUCCESS("\n✅ 이제 벡터 검색을 사용할 수 있습니다!")
            )
            self.stdout.write("예시:")
            self.stdout.write("  from shop.utils.embeddings import OpenAIEmbeddingGenerator")
            self.stdout.write("  generator = OpenAIEmbeddingGenerator()")
            self.stdout.write("  results = generator.search_similar_products('노트북')")
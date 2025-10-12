import csv
from django.core.management.base import BaseCommand
from shop.models import Product


class Command(BaseCommand):
    help = 'Import products from CSV file with new structure including classification field'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                created_count = 0
                updated_count = 0
                
                for row in reader:
                    # CSV 컬럼명과 모델 필드 매핑
                    product_id = int(row['product_id'])
                    classification = row['classification']
                    category = row['category']
                    brand = row['brand']
                    name = row['name']
                    price = int(row['price'])
                    img = row['img']
                    
                    # if_affilated 컬럼의 TRUE/FALSE를 Boolean으로 변환
                    if_affiliated_str = row['if_affilated'].upper()
                    if_affiliated = if_affiliated_str == 'TRUE'
                    
                    reviews = row['reviews']
                    
                    # Product 객체 생성 또는 업데이트
                    product, created = Product.objects.get_or_create(
                        id=product_id,
                        defaults={
                            'classification': classification,
                            'category': category,
                            'brand': brand,
                            'name': name,
                            'price': price,
                            'img': img,
                            'if_affiliated': if_affiliated,
                            'reviews': reviews,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created product: {product.name}')
                        )
                    else:
                        # 기존 제품 업데이트
                        product.classification = classification
                        product.category = category
                        product.brand = brand
                        product.name = name
                        product.price = price
                        product.img = img
                        product.if_affiliated = if_affiliated
                        product.reviews = reviews
                        product.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'Updated product: {product.name}')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Import completed! Created: {created_count}, Updated: {updated_count}'
                    )
                )
                
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'File not found: {csv_file_path}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing products: {str(e)}')
            )
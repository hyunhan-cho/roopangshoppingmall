import csv
from django.core.management.base import BaseCommand, CommandError
from shop.models import Product

class Command(BaseCommand):
    help = 'CSV에서 상품 데이터를 임포트합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='CSV 파일 경로')
        parser.add_argument('--truncate', action='store_true', help='기존 데이터를 비우고 재삽입')

    def handle(self, *args, **options):
        path = options['file']
        truncate = options['truncate']

        try:
            if truncate:
                Product.objects.all().delete()
                self.stdout.write(self.style.WARNING('기존 Product 데이터 삭제 완료'))

            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    try:
                        # CSV 컬럼 매핑
                        product, created = Product.objects.update_or_create(
                            id=int(row.get('product_id') or 0),
                            defaults={
                                'classification': row.get('classification') or '생활용품',
                                'category': row.get('category') or '',
                                'brand': row.get('brand') or '',
                                'name': row.get('name') or '',
                                'price': int(float(row.get('price') or 0)),
                                'img': row.get('img') or '',
                                'if_affiliated': str(row.get('if_affilated', '')).strip().upper() == 'TRUE',
                                'reviews': row.get('reviews') or '',
                            }
                        )
                        count += 1
                    except Exception as ie:
                        self.stdout.write(self.style.ERROR(f"행 처리 오류: {ie} | 데이터: {row}"))

            self.stdout.write(self.style.SUCCESS(f"임포트 완료: {count}개 행 처리"))
        except FileNotFoundError:
            raise CommandError(f"파일을 찾을 수 없습니다: {path}")
        except Exception as e:
            raise CommandError(str(e))

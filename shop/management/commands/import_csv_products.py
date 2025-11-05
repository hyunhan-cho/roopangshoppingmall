import csv
from django.core.management.base import BaseCommand, CommandError
from shop.models import Product


def _parse_price(value: str) -> int:
    """문자열 가격을 정수로 파싱 (쉼표, 공백 허용). 빈값/오류는 0으로 처리."""
    if value is None:
        return 0
    s = str(value).strip()
    if not s:
        return 0
    # 1) 천단위 구분 쉼표 제거, 2) 공백 제거
    s = s.replace(",", "").replace(" ", "")
    try:
        return int(float(s))
    except Exception:
        return 0


def _parse_bool(value) -> bool:
    """TRUE/False/1/0/yes/no 등 대소문자 무관 처리."""
    if value is None:
        return False
    s = str(value).strip().lower()
    return s in {"true", "1", "y", "yes"}

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
                created_cnt = 0
                updated_cnt = 0
                skipped_cnt = 0
                for row in reader:
                    try:
                        raw_id = row.get('product_id')
                        if not raw_id:
                            skipped_cnt += 1
                            self.stdout.write(self.style.WARNING(f"product_id 누락으로 스킵: {row}"))
                            continue

                        pid = int(str(raw_id).strip())

                        defaults = {
                            'classification': row.get('classification') or '생활용품',
                            'category': (row.get('category') or '').strip(),
                            'brand': (row.get('brand') or '').strip(),
                            'name': (row.get('name') or '').strip(),
                            'price': _parse_price(row.get('price')),
                            'img': (row.get('img') or '').strip(),
                            'if_affiliated': _parse_bool(row.get('if_affilated')),
                            'reviews': row.get('reviews') or '',
                        }

                        product, created = Product.objects.update_or_create(
                            id=pid,
                            defaults=defaults,
                        )
                        if created:
                            created_cnt += 1
                        else:
                            updated_cnt += 1
                    except Exception as ie:
                        skipped_cnt += 1
                        self.stdout.write(self.style.ERROR(f"행 처리 오류: {ie} | 데이터: {row}"))

            self.stdout.write(self.style.SUCCESS(
                f"임포트 완료 - 생성: {created_cnt}개, 업데이트: {updated_cnt}개, 스킵: {skipped_cnt}개"
            ))
        except FileNotFoundError:
            raise CommandError(f"파일을 찾을 수 없습니다: {path}")
        except Exception as e:
            raise CommandError(str(e))

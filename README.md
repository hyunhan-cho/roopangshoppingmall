# 루팡! - 제휴 브랜드 추천시스템 연구용 쇼핑몰

한국외국어대학교 미디어커뮤니케이션학부 "알고리즘미디어와 사회" 수업 7조 프로젝트

## 🎯 연구 목적

제휴 브랜드 중심 추천시스템 조작에 대한 소비자 반응 분석을 위한 실험용 쇼핑몰입니다.

## 🛠 기술 스택

- **백엔드**: Django 5.2.7
- **데이터베이스**: Supabase (PostgreSQL + pgvector)
- **AI**: OpenAI Embedding API (text-embedding-3-small)
- **프론트엔드**: HTML/CSS/JavaScript (쿠팡 스타일 UI)

## 📁 주요 기능

- ✅ IRB 스타일 연구 참여 동의서
- ✅ 실제 상품 데이터 (30개 문구용품)
- ✅ 장바구니 기능
- ✅ OpenAI 기반 벡터 유사도 검색
- ✅ 제휴 브랜드 우선 AI 추천 시스템
- ✅ 참여자 행동 데이터 수집

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/hyunhan-cho/roopangshoppingmall.git
cd roopangshoppingmall
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv myvenv
# Windows
myvenv\\Scripts\\activate
# macOS/Linux
source myvenv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 열어서 실제 값으로 수정:
# - OPENAI_API_KEY: OpenAI API 키
# - SUPABASE_PASSWORD: Supabase 데이터베이스 비밀번호
```

### 5. 데이터베이스 마이그레이션
```bash
python manage.py migrate --database=direct
```

### 6. 상품 데이터 임포트
```bash
python manage.py import_csv_products --file "쇼핑몰 상품데이터 팀 공용 - 쇼핑몰 상품데 - stationery_products_final_korean (1).csv.csv"
```

### 7. AI 임베딩 생성
```bash
python manage.py create_embeddings --force
```

### 8. 서버 실행
```bash
python manage.py runserver
```

📱 **접속**: http://127.0.0.1:8000/

## 📊 실험 흐름

1. **동의서** (/) → 참여자 정보 입력 및 연구 동의
2. **상품 탐색** (/shop/) → 상품 검색 및 장바구니 담기
3. **AI 추천** (/shop/cart/) → 장바구니 기반 제휴 상품 추천
4. **데이터 수집** → 참여자 행동 패턴 및 선택 분석

## 🤖 AI 추천 시스템 특징

- **벡터 임베딩**: OpenAI text-embedding-3-small (1536차원)
- **유사도 검색**: 코사인 유사도 기반
- **제휴 상품 우선**: `if_affiliated=True` 상품만 추천
- **카테고리 연관성**: 장바구니 상품과 같은 카테고리 우선
- **pgvector 최적화**: PostgreSQL 벡터 확장으로 고성능 검색

## 📁 프로젝트 구조

```
shoppingmall/
├── config/                 # Django 설정
├── shop/                   # 메인 앱
│   ├── models.py          # Product, Participant 모델
│   ├── views.py           # 뷰 로직 및 API
│   ├── utils/
│   │   └── embeddings.py  # OpenAI 임베딩 클래스
│   ├── management/commands/
│   │   ├── import_csv_products.py
│   │   └── create_embeddings.py
│   └── templates/shop/    # HTML 템플릿
├── .env.example           # 환경변수 템플릿
└── requirements.txt       # Python 패키지 목록
```

## 🔧 관리 명령어

```bash
# CSV 상품 데이터 임포트
python manage.py import_csv_products --file data.csv --truncate

# 임베딩 생성 (전체)
python manage.py create_embeddings --force

# 임베딩 생성 (특정 상품)
python manage.py create_embeddings --product-ids 1 2 3

# 임베딩 생성 (배치 크기 설정)
python manage.py create_embeddings --batch-size 5
```

## 🧪 실험 설정

### 조작 변인
- **제휴 브랜드 우선 추천**: AI 추천 시 제휴 상품(`if_affiliated=True`)만 결과에 포함
- **카테고리 연관성**: 장바구니 상품 카테고리와 일치하는 상품 우선 추천

### 종속 변인
- 추천 상품 클릭률
- 장바구니 담기 전환율
- 제휴 vs 비제휴 상품 선택 비율
- 체류 시간 및 탐색 패턴

## 👥 팀 정보

- **개발자**: 조현한 (010-5779-1297, hyeonhanjo1@gmail.com)
- **지도교수**: 이상욱 교수님
- **소속**: 한국외국어대학교 미디어커뮤니케이션학부
- **과목**: 알고리즘미디어와 사회 (7조)

## ⚠️ 주의사항

1. **API 키 보안**: `.env` 파일을 절대 커밋하지 마세요
2. **연구 윤리**: 수집된 데이터는 연구 목적으로만 사용
3. **성능**: 임베딩 생성 시 OpenAI API 사용량 확인

## 📄 라이선스

이 프로젝트는 연구 목적으로만 사용됩니다.
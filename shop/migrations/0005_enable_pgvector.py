from django.db import migrations


def enable_pgvector(apps, schema_editor):
    # PostgreSQL에서만 확장 설치
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")


def noop(apps, schema_editor):
    # 되돌릴 작업 없음
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_product_description_embedding_product_name_embedding_and_more'),
    ]

    operations = [
        migrations.RunPython(enable_pgvector, noop),
    ]

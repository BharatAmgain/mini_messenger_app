from django.db import migrations


def verify_column_exists(apps, schema_editor):
    # This function does nothing - it's a no-op
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),  # Your first migration
    ]

    operations = [
        migrations.RunPython(verify_column_exists),
    ]
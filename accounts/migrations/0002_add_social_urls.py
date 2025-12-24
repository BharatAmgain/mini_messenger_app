# accounts/migrations/0002_add_social_urls.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='facebook_url',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='twitter_url',
            field=models.URLField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='customuser',
            name='instagram_url',
            field=models.URLField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='customuser',
            name='linkedin_url',
            field=models.URLField(blank=True, max_length=200),
        ),
    ]
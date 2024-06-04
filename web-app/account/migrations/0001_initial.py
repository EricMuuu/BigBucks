# Generated by Django 4.2.9 on 2024-03-22 04:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=20)),
                ('first_name', models.CharField(default='Bob', max_length=20)),
                ('last_name', models.CharField(default='Allen', max_length=20)),
                ('phone', models.CharField(default='1234567890', max_length=10)),
                ('email', models.EmailField(default='example@example.com', max_length=254)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

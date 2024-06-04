# Generated by Django 4.2.9 on 2024-03-27 01:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='cash',
            field=models.BigIntegerField(default=1000000),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_administrator',
            field=models.BooleanField(default=False),
        ),
    ]
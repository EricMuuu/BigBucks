# Generated by Django 4.2.9 on 2024-04-12 05:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_userprofile_cash_userprofile_is_administrator'),
        ('asset', '0003_alter_asset_date_alter_asset_symbol'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserStockPortfolio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=10)),
                ('total_shares', models.IntegerField(default=0)),
                ('avg_price', models.FloatField(default=0.0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_portfolios', to='account.userprofile')),
            ],
            options={
                'unique_together': {('user', 'symbol')},
            },
        ),
    ]

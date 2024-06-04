from django.db import models
from account.models import *
from django.utils import timezone


# Create your models here.
# SPY 5 years index data
class Index(models.Model):
    date = models.DateField(unique=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.BigIntegerField()

    def __str__(self):
        return f"{self.date} - Close: {self.close}"

# Data of each asset owned by users
class Asset(models.Model):
    date = models.DateField()
    #TODO: check if should set unique to True
    symbol = models.CharField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.BigIntegerField()

    def __str__(self):
        return f"{self.date} - Close: {self.close}"

# Relationship between user and asset
# Orders
class UserAsset(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    share_num = models.IntegerField(default=1)
    purchase_date = models.DateTimeField(default=timezone.now)


# Keep track of total shares a user owns for each share
class UserStockPortfolio(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='stock_portfolios')
    symbol = models.CharField(max_length=10)
    total_shares = models.IntegerField(default=0)
    # average purchase price
    avg_price = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('user', 'symbol')

    def __str__(self):
        return f"{self.user} owns {self.total_shares} shares of {self.symbol}"

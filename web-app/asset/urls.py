from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('index/', views.index_data, name='index'),
    path('buy/', views.buy, name='buy'),
    path('sell/', views.sell, name='sell'),
    path('portfolio_performance/', views.portfolio_performance, name='portfolio_performance'),
    path('historical_data_owned/', views.historical_data_owned, name = "historical_data_owned"),
    path('show_user_asset_shares/', views.show_user_asset_shares, name = "dashboard"),
    path('administrator_list_all_stocks/', views.administrator_list_all_stocks, name = "administrator_list_all_stocks"),
    path('administrator_risk_analysis/', views.administrator_risk_analysis, name = "administrator_risk_analysis"),
    path('get_latest_price/<str:symbol>/', views.get_latest_price, name='get_latest_price'),
    path('admin/market-orders/', views.administrator_market_orders_summary, name='administrator_market_orders_summary'),
    path('graph-selection/', views.graph_selection, name='graph_selection'),
    path('stock-time-series/', views.stock_time_series, name='stock_time_series'),
    path('daily-simple-return/', views.daily_simple_return, name='daily_simple_return'),
    path('daily-return-vs-previous/', views.daily_return_vs_previous, name='daily_return_vs_previous'),
    path('histogram-daily-returns/', views.histogram_daily_returns, name='histogram_daily_returns'),
    path('stock-price-vs-index/', views.stock_price_vs_index, name='stock_price_vs_index'),
    path('daily-return-vs-index/', views.daily_return_vs_index, name='daily_return_vs_index'),
    path('scatter-stock-vs-index/', views.scatter_stock_vs_index, name='scatter_stock_vs_index'),
    path('efficient_frontier/', views.efficient_frontier, name='efficient_frontier'),
]
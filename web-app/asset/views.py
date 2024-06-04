from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login
from django.db.models.functions import Abs

from django.urls import reverse
from account.models import UserProfile
from django.db.models import Q
from account.views import *
from .models import *
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime
from .forms import *
from django.utils import timezone

from config import api_key
import pandas as pd
import numpy as np
from portfolio_analysis.portfolio_analysis import ret_vol_cal, opt_vol_given_ret, sharpe_cal, portfolio_performance_cal
from portfolio_analysis.visualization import plot_efficient_frontier_img
from django.db.models import Sum
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.db.models import F
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import timedelta

def acquire_data(key, symbol = "SPY"):
    symbol = symbol.upper()
    ts = TimeSeries(key=key, output_format='pandas')
    data, meta_data = ts.get_daily_adjusted(symbol=symbol, outputsize='full')
    data = data.last('5Y')
    if data is None:
        return None
    return data

def update_data(key, symbol = "SPY"):
    # By default we update the data for the S&P 500 index
    symbol = symbol.upper()
    asset = Asset.objects.filter(symbol=symbol).order_by('-date')
    latest_data = asset.first()
    # print(latest_data.date, datetime.today().date())
    if latest_data and latest_data.date == datetime.today().date():
        return
    else:
        data = acquire_data(key, symbol)
        # Asset.objects.filter(symbol=symbol).delete()
        # print("Update data for symbol: ", symbol)
        for index, row in data.iterrows():
            Asset.objects.update_or_create(
                date=index,
                symbol=symbol,
                defaults={
                    'open': row['1. open'],
                    'high': row['2. high'],
                    'low': row['3. low'],
                    'close': row['5. adjusted close'],
                    'volume': row['6. volume']
                }
            )
    return 

        
            
@login_required
@csrf_exempt
def index_data(request):
    ts = TimeSeries(key=api_key, output_format='pandas')
    # If the data in our database is up to date (lastest date in the database is today) we use the data in the database, otherwise we pull from the API and update our database and then display it
    update_data(api_key)
    data = Asset.objects.filter(symbol="SPY").order_by('-date')
    context = {
        'spy_data': data,
    }
    return render(request, 'asset/index.html', context)



@login_required
@csrf_exempt
def historical_data_owned(request):
    user_profile = UserProfile.objects.get(user=request.user)
    for stock in UserStockPortfolio.objects.filter(user=user_profile):
        update_data(api_key, stock.symbol)
    price_df = get_user_assets(user_profile)
    price_df = price_df.sort_index(ascending=False)
    
    price_df = price_df.reset_index().rename(columns = {'date': 'Date'})
    price_df_list = price_df.to_dict('records')
    context = {
        'price_df': price_df_list
    }
    
    return render(request, 'asset/historical_data_owned.html', context)


@login_required
@csrf_exempt
def buy(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = BuySellForm(request.POST)
        if form.is_valid():
            symbol = form.cleaned_data['symbol']
            share_num = form.cleaned_data['share_num']
            price = fetch_latest_price(symbol)
            if price == None:
                messages.error(request, 'Symbol does not exist!', extra_tags='danger')
                return render(request, 'asset/buy.html', {'form': form})
            if process_buy_order(user_profile, symbol, share_num, price):
                messages.success(request, 'Shares bought successfully!', extra_tags='success')
            else:
                messages.error(request, 'Insufficient funds to complete the transaction.', extra_tags='danger')
    else:
        form = BuySellForm()
    return render(request, 'asset/buy.html', {'form': form})

@login_required
@require_GET
def get_latest_price(request, symbol):
    price = fetch_latest_price(symbol)
    return HttpResponse(price, content_type='text/plain')

@login_required
@csrf_exempt
def sell(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = BuySellForm(request.POST)
        if form.is_valid():
            symbol = form.cleaned_data['symbol']
            share_num = form.cleaned_data['share_num']
            price = fetch_latest_price(symbol)
            if price == None:
                messages.error(request, 'Symbol does not exist!', extra_tags='danger')
                return render(request, 'asset/sell.html', {'form': form})
            if process_sell_order(user_profile, symbol, share_num, price):
                messages.success(request, 'Shares sold successfully!', extra_tags='success')
            else:
                messages.error(request, 'Insufficient shares to complete the transaction.', extra_tags='danger')
    else:
        form = BuySellForm()
    return render(request, 'asset/sell.html', {'form': form})


def fetch_latest_price(symbol):
    try:
        update_data(api_key, symbol)
        asset = Asset.objects.filter(symbol=symbol.upper()).latest('date')
        return asset.close
    except Asset.DoesNotExist:
        return None
    except Exception as e:
        print(f"An error occurred while fetching the latest price for {symbol}: {str(e)}")
        return None



def process_buy_order(user_profile, symbol, share_num, price):
    symbol = symbol.upper()
    total_cost = price * share_num
    if user_profile.cash >= total_cost:
        user_profile.cash -= total_cost
        user_profile.save()
        
        # Store the 5-year stock info in database
        update_data(api_key, symbol)
        asset = Asset.objects.filter(symbol=symbol).latest('date')
        user_asset, created = UserAsset.objects.get_or_create(user=user_profile, asset=asset, share_num = share_num, purchase_date=timezone.now())
        
        # Update or create the user's stock portfolio for aggregated data
        portfolio, created = UserStockPortfolio.objects.get_or_create(
            user=user_profile,
            symbol=symbol,
            defaults={'total_shares': 0, 'avg_price': price}
        )
        if not created:
            # Calculate new average price and total shares
            new_total_shares = portfolio.total_shares + share_num
            new_total_value = (portfolio.avg_price * portfolio.total_shares) + (price * share_num)
            portfolio.avg_price = new_total_value / new_total_shares
            portfolio.total_shares = new_total_shares
        else:
            portfolio.total_shares = share_num
        
        portfolio.save()
        return True
    return False

def process_sell_order(user_profile, symbol, share_num, price):
    symbol = symbol.upper()
    try:
        stock = UserStockPortfolio.objects.get(user=user_profile, symbol=symbol)
        if stock.total_shares >= share_num:
            total_earnings = price * share_num
            user_profile.cash += total_earnings

            # Log the sell transaction
            update_data(api_key, symbol)
            asset = Asset.objects.filter(symbol=symbol).latest('date')
            UserAsset.objects.create(
                user=user_profile,
                asset=asset,
                share_num=-share_num,  # Negative to indicate a sell
                purchase_date=timezone.now()
            )

            # Update aggregate data
            stock.total_shares -= share_num
            user_profile.save()
            if stock.total_shares == 0:
                stock.delete()
            else:
                stock.save()
                
            return True
        else:
            return False
    except UserStockPortfolio.DoesNotExist:
        return False

#TODO: 
def get_user_assets(user_profile):
    user_portfolios = UserStockPortfolio.objects.filter(user=user_profile).order_by('symbol')
    
    final_df = None
    for portfolio in user_portfolios:
        asset_data = Asset.objects.filter(symbol=portfolio.symbol).order_by('date').values('date', 'close')
        asset_df = pd.DataFrame(list(asset_data))
        asset_df.set_index('date', inplace=True)
        asset_df.rename(columns={'close': portfolio.symbol}, inplace=True)
        
        if final_df is None:
            final_df = asset_df
        else:
            final_df = pd.merge(final_df, asset_df, left_index=True, right_index=True, how='outer')

    if final_df is None:
        final_df = pd.DataFrame()

    return final_df

#TODO: filter out buy symbol not row
def get_user_asset_shares(user_profile):
    user_portfolios = UserStockPortfolio.objects.filter(user=user_profile)
    shares_list = [portfolio.total_shares for portfolio in user_portfolios]
    
    return np.array(shares_list)

def get_user_asset_names(user_profile):
    user_assets = UserAsset.objects.filter(user=user_profile)
    assets_list = []
    for user_asset in user_assets:
        assets_list.append(user_asset.asset.symbol)
    
    return np.array(assets_list)

@login_required
@csrf_exempt
def show_user_asset_shares(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    # Use new table
    portfolios = UserStockPortfolio.objects.filter(user=user_profile).order_by('symbol')
    assets_shares_list = [(portfolio.symbol, portfolio.total_shares) for portfolio in portfolios]

    context = {
        "assets_shares_list": assets_shares_list
    }
    return render(request, 'account/dashboard.html', context)

        
@login_required
@csrf_exempt
def portfolio_performance(request, return_targets = np.round(np.linspace(0.01, 0.4, 100), 4)):
    user_profile = UserProfile.objects.get(user=request.user)
    price_df = get_user_assets(user_profile)
    if price_df.empty:
        context = {'message': "You currently do not hold any assets"}
        return render(request, 'account/dashboard.html', context)
    account_shares = get_user_asset_shares(user_profile)
    
    # Compute the Sharpe Ratio
    sharpe_ratio = sharpe_cal(price_df, account_shares)

    # Compute other needed data for the page
    names = list(price_df.columns)
    anl_ex_ret_df, anl_vol_df = ret_vol_cal(price_df)
    m_vol_results = []
    m_weight_results = []

    for target_ret in return_targets:
        m_vol, m_weights = opt_vol_given_ret(anl_ex_ret_df, anl_vol_df, target_ret)
        m_vol_results.append(m_vol)
        m_weight_results.append(m_weights)

    for i in range(len(m_weight_results)):
        try:
            m_weight_results[i] = [f"{element1}: {element2}" for element1, element2 in zip(names, m_weight_results[i])]
        except:
            continue

        
    combined_results = zip(return_targets, m_vol_results, m_weight_results)

    context = {
        'sharpe_ratio': sharpe_ratio,
        'combined_results': combined_results,
    }
    return render(request, 'asset/portfolio_performance.html', context)


# TODO: missing name of stock
@login_required
@csrf_exempt
def administrator_list_all_stocks(request):
    user_profile = UserProfile.objects.get(user=request.user)
    stocks_summary = UserStockPortfolio.objects.select_related('user').values(
        'symbol', 'total_shares', 'avg_price', 'user__username'
    ).order_by('symbol')  

    if user_profile.is_administrator ==  True:
        return render(request, 'asset/administrator_list_all_stocks.html', {'stocks': list(stocks_summary)})
    else:
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('dashboard')


@login_required
@csrf_exempt   
def administrator_market_orders_summary(request):
    user_profile = UserProfile.objects.get(user=request.user)
    now = timezone.now()
    adjusted_now = now + timedelta(hours=3)
    start_of_day = adjusted_now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = adjusted_now.replace(hour=23, minute=59, second=59, microsecond=999999)

    orders_today = UserAsset.objects.filter(purchase_date__range=(start_of_day, end_of_day)).select_related('asset', 'user').order_by('user__username')
    orders_list = []
    for order in orders_today:
        shares_bought = order.share_num if order.share_num > 0 else 0
        shares_sold = abs(order.share_num) if order.share_num < 0 else 0

        order_data = {
            'Symbol': order.asset.symbol,
            'User': order.user.username,
            'SharesBought': shares_bought, 
            'SharesSold': shares_sold       
        }
        orders_list.append(order_data)
    if user_profile.is_administrator:
        return render(request, 'asset/administrator_market_orders_summary.html', {'orders': orders_list})
    else:
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('dashboard')


    
    
@login_required
@csrf_exempt
def administrator_risk_analysis(request):
    user_profile = UserProfile.objects.get(user=request.user)
    all_price_df, stocks_info = get_all_users_assets()
    if 'Symbol' in stocks_info.columns and not stocks_info.empty:
        shares_dict = stocks_info.set_index('Symbol')['Total Shares'].to_dict()
        total_shares_ordered = [shares_dict.get(symbol, 0) for symbol in all_price_df.columns]
        account_shares = np.array(total_shares_ordered)
        all_portfolio_return, all_portfolio_volatility = portfolio_performance_cal(all_price_df, account_shares)

        if user_profile.is_administrator:
            context = {
                'All_portfolio_return': all_portfolio_return,
                'All_portfolio_volatility': all_portfolio_volatility
            }
            return render(request, 'asset/administrator_risk_analysis.html', context)
        else:
            messages.error(request, 'You are not authorized to view this page.')
            return redirect('dashboard')
    else:
        messages.error(request, 'No sufficient data to perform risk analysis.')
        return render(request, 'asset/administrator_risk_analysis.html', {'message': 'No sufficient data available for risk analysis.'})




def get_all_users_assets():
    """Get the dataframe of all users' assets historical prices."""
    all_portfolios = UserStockPortfolio.objects.all().order_by('symbol').distinct('symbol')
    
    final_df = None
    df_list = []
    for portfolio in all_portfolios:
        asset_data = Asset.objects.filter(symbol=portfolio.symbol).order_by('date').values('date', 'close')
        asset_df = pd.DataFrame(list(asset_data))
        asset_df.set_index('date', inplace=True)
        asset_df.rename(columns={'close': portfolio.symbol}, inplace=True)
        df_list.append(asset_df)
    
        if final_df is None:
            final_df = asset_df
        else:
            final_df = pd.merge(final_df, asset_df, left_index=True, right_index=True, how='outer')

    if final_df is None:
        final_df = pd.DataFrame()
    stocks_summary = UserStockPortfolio.objects.values('symbol').annotate(total_shares=Sum('total_shares')).order_by('symbol')
    stocks_info_df = pd.DataFrame(list(stocks_summary))
    stocks_info_df.rename(columns={'symbol': 'Symbol', 'total_shares': 'Total Shares'}, inplace=True)

    
    return final_df, stocks_info_df

def graph_selection(request):
    return render(request, 'asset/graph_selection.html')

# For graphs
def fetch_stock_data(symbol, api_key):
    ts = TimeSeries(key=api_key, output_format='pandas')
    try:
        data, _ = ts.get_daily_adjusted(symbol, outputsize='compact')
        if data.empty:
            return None
        data.sort_index(inplace=True)
        return data['5. adjusted close']
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# Figure 14.1
def plot_stock_data(df, symbol):
    plt.figure()
    plt.switch_backend('Agg')
    df.plot(title=f'Adjusted Close Prices for {symbol}')
    plt.xlabel('Date')
    plt.ylabel('Adjusted Close Price')
    plt.grid(True)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def stock_time_series(request):
    graph = None
    if request.method == 'POST':
        stock_symbol = request.POST.get('stock_symbol')
        df = fetch_stock_data(stock_symbol, api_key)
        if df is not None:
            graph = plot_stock_data(df, stock_symbol)
    return render(request, 'asset/stock_time_series.html', {'graph': graph})

# Figure 14.2
def daily_simple_return(request):
    graph = None
    if request.method == 'POST':
        stock_symbol = request.POST.get('stock_symbol')
        adjusted_close_prices = fetch_stock_data(stock_symbol, api_key)
        if adjusted_close_prices is not None:
            daily_returns = adjusted_close_prices.pct_change() * 100
            graph = plot_daily_return(daily_returns, stock_symbol)
    return render(request, 'asset/daily_simple_return.html', {'graph': graph})


def plot_daily_return(df, symbol):
    plt.figure()
    plt.scatter(df.index, df, alpha=0.5, s=100)
    plt.title(f'Daily Simple Returns for {symbol}')
    plt.xlabel('Date')
    plt.ylabel('Daily Simple Return (%)')
    plt.grid(True)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')


# Figure 14.3
def daily_return_vs_previous(request):
    graph = None
    if request.method == 'POST':
        stock_symbol = request.POST.get('stock_symbol')
        adjusted_close_prices = fetch_stock_data(stock_symbol, api_key)
        if adjusted_close_prices is not None:
            daily_returns = adjusted_close_prices.pct_change() * 100
            graph = plot_daily_return_vs_previous(daily_returns, stock_symbol)
    return render(request, 'asset/daily_return_vs_previous.html', {'graph': graph})

def plot_daily_return_vs_previous(daily_returns, symbol):
    plt.figure()
    plt.scatter(daily_returns[:-1], daily_returns[1:], alpha=0.5, s=100)
    plt.title(f'Daily Return vs. Previous Days Return for {symbol}')
    plt.xlabel('Previous Day\'s Return (%)')
    plt.ylabel('Today\'s Return (%)')
    plt.grid(True)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# Figure 14.4
def histogram_daily_returns(request):
    graph = None
    if request.method == 'POST':
        stock_symbol = request.POST.get('stock_symbol')
        adjusted_close_prices = fetch_stock_data(stock_symbol, api_key)
        if adjusted_close_prices is not None:
            daily_returns = adjusted_close_prices.pct_change()
            graph = plot_histogram_daily_returns(daily_returns, stock_symbol)
    return render(request, 'asset/histogram_daily_returns.html', {'graph': graph})

def plot_histogram_daily_returns(daily_returns, symbol):
    plt.figure(figsize=(10, 6))
    n, bins, patches = plt.hist(daily_returns, bins=20, alpha=0.75, color='blue', edgecolor='black')
    bin_labels = [f"{edge:.2%}" for edge in bins]
    plt.xticks(bins, bin_labels, rotation=90)

    plt.title(f'Histogram of Daily Returns for {symbol}')
    plt.xlabel('Daily Return (%)')
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=300)
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def fetch_data(stock_symbol, api_key):
    ts = TimeSeries(key=api_key, output_format='pandas')
    try:
        stock_data, _ = ts.get_daily_adjusted(stock_symbol, outputsize='compact')
        index_data, _ = ts.get_daily_adjusted('SPY', outputsize='compact')
        
        if stock_data.empty or index_data.empty:
            return None, None

        stock_data.sort_index(inplace=True)
        index_data.sort_index(inplace=True)
        stock_prices = stock_data['5. adjusted close']
        index_prices = index_data['5. adjusted close']
        
        return stock_prices, index_prices
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, None

# Stock price vs. Index price
def stock_price_vs_index(request):
    graph = None
    if request.method == 'POST':
        stock_symbol = request.POST.get('stock_symbol')
        stock_prices, index_prices = fetch_data(stock_symbol, api_key)
        if stock_prices is not None and index_prices is not None:
            graph = plot_stock_vs_index(stock_prices, index_prices, stock_symbol, 'SPY')
    return render(request, 'asset/stock_price_vs_index.html', {'graph': graph})

def plot_stock_vs_index(stock_prices, index_prices, stock_symbol, index_symbol):
    plt.figure(figsize=(10, 6))
    plt.plot(stock_prices.index, stock_prices, label=f'{stock_symbol} Price')
    plt.plot(index_prices.index, index_prices, label=f'{index_symbol} Price', alpha=0.75)
    plt.title(f'Stock Price vs. Index Price')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')


# Daily simply return vs index return over time
def daily_return_vs_index(request):
    graph = None
    if request.method == 'POST':
        stock_symbol = request.POST.get('stock_symbol')
        stock_prices, index_prices = fetch_data(stock_symbol, api_key)
        stock_returns = stock_prices.pct_change() * 100
        index_returns = index_prices.pct_change() * 100
        stock_returns = stock_returns[1:]
        index_returns = index_returns[1:]
        if stock_returns is not None and index_returns is not None:
            graph = plot_daily_return_vs_index(stock_returns, index_returns, stock_symbol, 'SPY')
    return render(request, 'asset/daily_return_vs_index.html', {'graph': graph})


def plot_daily_return_vs_index(stock_returns, index_returns, stock_symbol, index_symbol):
    plt.figure(figsize=(10, 6))
    plt.plot(stock_returns.index, stock_returns, label=f'{stock_symbol} Daily Return')
    plt.plot(index_returns.index, index_returns, label=f'{index_symbol} Daily Return', alpha=0.75)
    plt.title(f'Daily Return vs. Index Over Time')
    plt.xlabel('Date')
    plt.ylabel('Daily Return (%)')
    plt.legend()
    plt.grid(True)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')


# Daily simply return vs index return scatter
def scatter_stock_vs_index(request):
    graph = None
    if request.method == 'POST':
        stock_symbol = request.POST.get('stock_symbol')
        stock_prices, index_prices = fetch_data(stock_symbol, api_key)
        stock_returns = stock_prices.pct_change() * 100
        index_returns = index_prices.pct_change() * 100
        stock_returns = stock_returns[1:]
        index_returns = index_returns[1:]
        if stock_returns is not None and index_returns is not None:
            graph = plot_scatter_stock_vs_index(stock_returns, index_returns, stock_symbol, 'SPY')
    return render(request, 'asset/scatter_stock_vs_index.html', {'graph': graph})

def plot_scatter_stock_vs_index(stock_returns, index_returns, stock_symbol, index_symbol):
    plt.figure(figsize=(10, 6))
    plt.scatter(index_returns, stock_returns, alpha=0.5)
    plt.title(f'Scatter Plot of {stock_symbol} Returns vs. {index_symbol} Returns')
    plt.xlabel(f'{index_symbol} Returns (%)')
    plt.ylabel(f'{stock_symbol} Returns (%)')
    plt.grid(True)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# Efficient Frontier
@login_required
def efficient_frontier(request):
    user_profile = UserProfile.objects.get(user=request.user)
    price_df = get_user_assets(user_profile)
    shares = get_user_asset_shares(user_profile)
    return_targets = np.linspace(0.01, 0.4, 40)

    if request.method == 'POST':
        if not price_df.empty and shares.size > 0:
            graph = plot_efficient_frontier_and_current_portfolio(price_df, shares, return_targets)
            context = {'graph': graph}
            return render(request, 'asset/effcient_frontier.html', context)
        else:
            return render(request, 'asset/effcient_frontier.html', {'message': "You currently do not hold any assets or shares are not defined."})
    else:
        return render(request, 'asset/effcient_frontier.html')

def plot_efficient_frontier_and_current_portfolio(price_df, shares, return_targets):
    anl_ex_ret_df, anl_vol_df = ret_vol_cal(price_df)
    portfolio_return, portfolio_volatility, weights = [], [], []

    for target_ret in return_targets:
        vol, weight_vector = opt_vol_given_ret(anl_ex_ret_df, anl_vol_df, target_ret)
        if vol is not None:
            portfolio_return.append(target_ret)
            portfolio_volatility.append(vol)
            weights.append(weight_vector)

    current_portfolio_return, current_portfolio_volatility = portfolio_performance_cal(price_df, shares)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(portfolio_volatility, portfolio_return, 'b-', label='Efficient Frontier')
    ax.scatter([current_portfolio_volatility], [current_portfolio_return], color='red', label='Current Portfolio', zorder=5)
    ax.set_title('Efficient Frontier and Current Portfolio Position')
    ax.set_xlabel('Volatility (Standard Deviation)')
    ax.set_ylabel('Expected Return')
    ax.legend(loc='best')
    ax.grid(True)

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    
    return base64.b64encode(buf.getvalue()).decode('utf-8')

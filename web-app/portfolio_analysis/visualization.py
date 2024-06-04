import matplotlib.pyplot as plt
from io import BytesIO

def plot_efficient_frontier_img(portfolio_return, portfolio_volatility):
    fig, ax = plt.subplots()
    ax.scatter(portfolio_return[:-1], portfolio_volatility[:-1], label='Portfolios')
    ax.scatter(portfolio_return[-1], portfolio_volatility[-1], color='red', label='Target Portfolio', edgecolors='black', s=100)
    ax.set_title('Portfolio Return vs. Volatility')
    ax.set_xlabel('Return')
    ax.set_ylabel('Volatility')
    ax.legend()
    ax.grid(True)
    img_bytes = BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close(fig)
    img_bytes.seek(0)
    
    return img_bytes

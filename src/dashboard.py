import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# GraphQL endpoint
ENDPOINT = "http://localhost:8080/v1/graphql"

RECOVERY_BLOCKS_LIMIT = 30

BOT = "0x9d01928fBcc737e6Ae22466C09981b2f90524780" # has 2m txs

def shorten_address(address):
    """Shorten Ethereum address to 0xabcd...abcd format"""
    return f"{address[:6]}...{address[-4:]}"

def calculate_recovery_times(df):
    """Calculate how many blocks it took for price to recover after each swap"""
    recovery_times = []
    max_blocks_to_check = 100  # Maximum number of blocks to look ahead
    price_threshold = 0.00025  # 0.025% threshold
    
    # Sort by block number to ensure chronological order
    df = df.sort_values('block_number')
    
    for i in range(len(df) - 1):
        current_price = df.iloc[i]['actual_price']
        current_block = df.iloc[i]['block_number']
        
        # Look ahead for price recovery
        for j in range(i + 1, min(i + max_blocks_to_check, len(df))):
            future_price = df.iloc[j]['actual_price']
            future_block = df.iloc[j]['block_number']
            
            # Calculate price difference percentage
            price_diff = abs(future_price - current_price) / current_price
            
            if price_diff <= price_threshold:
                recovery_times.append(future_block - current_block)
                break
    
    return recovery_times

def fetch_swaps():
    query = """
    {
        AlgebraPool_Swap(where: {_not: {sender: {_eq: "0x9d01928fBcc737e6Ae22466C09981b2f90524780"}}}) {
            sender
            amount0
            amount1
            price
            id
        }
    }
    """
    
    try:
        response = requests.post(ENDPOINT, json={'query': query})
        response.raise_for_status()  # Raise an exception for bad status codes
        
        result = response.json()
        
        # Check for GraphQL errors
        if 'errors' in result:
            print("GraphQL Errors:", result['errors'])
            return []
            
        # Check if data exists and has the expected structure
        if 'data' not in result or 'AlgebraPool_Swap' not in result['data']:
            print("Unexpected response structure:", result)
            return []
            
        return result['data']['AlgebraPool_Swap']
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def create_dashboard():
    # Fetch data
    swaps = fetch_swaps()
    
    if not swaps:
        print("No data available to create dashboard")
        return
        
    df = pd.DataFrame(swaps)
    
    # Convert amounts to float and handle negative values
    decimals = 6
    df['amount0'] = df['amount0'].astype(float).abs() / 10**decimals
    df['amount1'] = df['amount1'].astype(float).abs() / 10**decimals
    
    # Convert price to float and calculate actual price
    df['price'] = df['price'].astype(float)
    df['actual_price'] = df['price'] / (2**96)  # Convert from Q96.96 format
    
    # Extract block number from ID (format: chainId_blockNumber_logIndex)
    df['block_number'] = df['id'].str.split('_').str[1].astype(int)
    
    # Create block ranges (e.g., every 1000 blocks)
    block_range_size = 1000
    df['block_range'] = (df['block_number'] // block_range_size) * block_range_size
    
    # Calculate price recovery times
    recovery_times = calculate_recovery_times(df)
    
    # Filter recovery times to 0-RECOVERY_BLOCKS_LIMIT range
    recovery_times = [t for t in recovery_times if 0 <= t <= RECOVERY_BLOCKS_LIMIT]
    
    # Create custom bins for the histogram
    bins = [0, 1, 2, 3] + list(range(5, 101, 5))
    
    # Create subplots
    fig = make_subplots(
        rows=5, cols=1,
        subplot_titles=(
            "Swap Count Per Sender Distribution",
            "Swap Amount Distribution",
            "Swap Count in Block Ranges",
            "Price Over Time",
            "Price Recovery Time Distribution (0-100 blocks)"
        ),
        vertical_spacing=0.1
    )
    
    # 1. Swap Count Per Sender Distribution
    sender_counts = df['sender'].value_counts().head(20)
    print(sender_counts)
    
    # Create shortened addresses for display
    shortened_addresses = {addr: shorten_address(addr) for addr in sender_counts.index}
    
    fig.add_trace(
        go.Bar(
            x=[shortened_addresses[addr] for addr in sender_counts.index],
            y=sender_counts.values,
            name="Swaps per Sender",
            hovertemplate="Address: %{customdata}<br>Swaps: %{y}<extra></extra>",
            customdata=sender_counts.index
        ),
        row=1, col=1
    )
    
    # 2. Swap Amount Distribution
    fig.add_trace(
        go.Histogram(
            x=df['amount0'],
            name="Amount0 Distribution",
            nbinsx=50
        ),
        row=2, col=1
    )
    
    # 3. Swap Count in Block Ranges
    block_counts = df.groupby('block_range').size()
    fig.add_trace(
        go.Bar(
            x=block_counts.index,
            y=block_counts.values,
            name="Swaps per Block Range"
        ),
        row=3, col=1
    )
    
    # 4. Price Over Time
    fig.add_trace(
        go.Scatter(
            x=df['block_number'],
            y=df['actual_price'],
            mode='lines',
            name="Price",
            line=dict(width=1)
        ),
        row=4, col=1
    )
    
    # 5. Price Recovery Time Distribution
    fig.add_trace(
        go.Histogram(
            x=recovery_times,
            name="Recovery Time",
            xbins=dict(
                start=0,
                end=RECOVERY_BLOCKS_LIMIT,
                size=1  # 1-block intervals for 0-3
            ),
            hovertemplate="Blocks: %{x:.0f}<br>Count: %{y}<extra></extra>",
            autobinx=False,
        ),
        row=5, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=1800,
        showlegend=False,
        title_text="Algebra Pool Swaps Dashboard",
        title_x=0.5
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Sender Address", row=1, col=1)
    fig.update_yaxes(title_text="Number of Swaps", row=1, col=1)
    
    fig.update_xaxes(title_text="Swap Amount", row=2, col=1)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    
    fig.update_xaxes(title_text="Block Range", row=3, col=1)
    fig.update_yaxes(title_text="Number of Swaps", row=3, col=1)
    
    fig.update_xaxes(title_text="Block Number", row=4, col=1)
    fig.update_yaxes(title_text="Price (token1/token0)", row=4, col=1)
    
    fig.update_xaxes(
        title_text="Blocks to Recover",
        range=[0, 100],
        row=5, col=1
    )
    fig.update_yaxes(title_text="Number of Swaps", row=5, col=1)
    
    # Save as HTML
    fig.write_html("swaps_dashboard.html")
    print("Dashboard saved as swaps_dashboard.html")

if __name__ == "__main__":
    create_dashboard() 
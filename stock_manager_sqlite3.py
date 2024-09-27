import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from sqlite3 import Error
from contextlib import contextmanager

# Constants
DB_NAME = 'stocks.db'

# Database Helper Functions

@contextmanager
def get_db_connection(db_name=DB_NAME):
    """Context manager for SQLite database connection."""
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        conn.execute("PRAGMA foreign_keys = 1")  # Enable foreign key support
        yield conn
    except Error as e:
        st.error(f"Database connection error: {e}")
        yield None
    finally:
        if conn:
            conn.close()

def init_db():
    """Initialize the database and create tables if they don't exist."""
    with get_db_connection() as conn:
        if conn is not None:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_symbol TEXT NOT NULL UNIQUE,
                total_shares INTEGER NOT NULL,
                buy_price REAL NOT NULL,
                risk_ratio REAL NOT NULL,
                reward_ratio REAL NOT NULL,
                sell_strategy TEXT NOT NULL,
                sell_price REAL
            );
            """
            try:
                conn.execute(create_table_sql)
            except Error as e:
                st.error(f"Error creating table: {e}")

def add_stock_entry(entry):
    """Add a new stock entry to the database."""
    with get_db_connection() as conn:
        if conn is not None:
            insert_sql = """
            INSERT INTO stocks (stock_symbol, total_shares, buy_price, risk_ratio, reward_ratio, sell_strategy, sell_price)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """
            try:
                conn.execute(insert_sql, (
                    entry['stock_symbol'],
                    entry['total_shares'],
                    entry['buy_price'],
                    entry['risk_ratio'],
                    entry['reward_ratio'],
                    entry['sell_strategy'],
                    entry['sell_price']
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                st.error(f"Stock Symbol '{entry['stock_symbol']}' already exists. Please use a unique symbol.")
                return False
            except Error as e:
                st.error(f"Error adding stock entry: {e}")
                return False
        else:
            st.error("Failed to connect to the database.")
            return False

def get_all_stocks():
    """Retrieve all stock entries from the database."""
    with get_db_connection() as conn:
        stocks = []
        if conn is not None:
            select_sql = "SELECT * FROM stocks;"
            try:
                cursor = conn.execute(select_sql)
                rows = cursor.fetchall()
                for row in rows:
                    stock = {
                        'id': row[0],
                        'stock_symbol': row[1],
                        'total_shares': row[2],
                        'buy_price': row[3],
                        'risk_ratio': row[4],
                        'reward_ratio': row[5],
                        'sell_strategy': row[6],
                        'sell_price': row[7]
                    }
                    stocks.append(stock)
            except Error as e:
                st.error(f"Error retrieving stocks: {e}")
        else:
            st.error("Failed to connect to the database.")
        return stocks

def update_stock_entry(stock_id, updated_entry):
    """Update an existing stock entry in the database."""
    with get_db_connection() as conn:
        if conn is not None:
            update_sql = """
            UPDATE stocks
            SET stock_symbol = ?,
                total_shares = ?,
                buy_price = ?,
                risk_ratio = ?,
                reward_ratio = ?,
                sell_strategy = ?,
                sell_price = ?
            WHERE id = ?;
            """
            try:
                conn.execute(update_sql, (
                    updated_entry['stock_symbol'],
                    updated_entry['total_shares'],
                    updated_entry['buy_price'],
                    updated_entry['risk_ratio'],
                    updated_entry['reward_ratio'],
                    updated_entry['sell_strategy'],
                    updated_entry['sell_price'],
                    stock_id
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                st.error(f"Stock Symbol '{updated_entry['stock_symbol']}' already exists. Please use a unique symbol.")
                return False
            except Error as e:
                st.error(f"Error updating stock entry: {e}")
                return False
        else:
            st.error("Failed to connect to the database.")
            return False

def delete_stock_entry(stock_id):
    """Delete a stock entry from the database."""
    with get_db_connection() as conn:
        if conn is not None:
            delete_sql = "DELETE FROM stocks WHERE id = ?;"
            try:
                conn.execute(delete_sql, (stock_id,))
                conn.commit()
                return True
            except Error as e:
                st.error(f"Error deleting stock entry: {e}")
                return False
        else:
            st.error("Failed to connect to the database.")
            return False

# Calculation Function using pandas and numpy

def calculate_metrics(total_shares, buy_price, risk_ratio, reward_ratio, sell_strategy):
    """Calculate financial metrics based on input parameters."""
    total_investment = total_shares * buy_price
    risk_amount = buy_price * (risk_ratio / 100)
    reward_amount = buy_price * (reward_ratio / 100)
    stop_loss_price = buy_price - risk_amount
    take_profit_price = buy_price + reward_amount

    if sell_strategy == "Risk-Based":
        adjusted_sell_price = stop_loss_price
    else:
        adjusted_sell_price = take_profit_price

    return pd.Series({
        'Total Investment ($)': np.round(total_investment, 2),
        'Risk Amount ($)': np.round(risk_amount, 2),
        'Reward Amount ($)': np.round(reward_amount, 2),
        'Stop-Loss Price ($)': np.round(stop_loss_price, 2),
        'Take-Profit Price ($)': np.round(take_profit_price, 2),
        'Adjusted Sell Price ($)': np.round(adjusted_sell_price, 2)
    })

def plot_comparison_chart(df, metrics, title):
    """
    Plot a consolidated bar chart comparing multiple metrics across all stocks.

    Parameters:
    - df: DataFrame containing stock data and metrics.
    - metrics: List of metrics to compare.
    - title: Title of the chart.
    """
    x = np.arange(len(df['stock_symbol']))  # Label locations
    width = 0.2  # Width of each bar

    fig, ax = plt.subplots(figsize=(12, 7))

    for i, metric in enumerate(metrics):
        ax.bar(x + i*width - width, df[metric], width, label=metric)

    ax.set_xlabel('Stock Symbol')
    ax.set_ylabel('Amount ($)')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(df['stock_symbol'], rotation=45)
    ax.legend()

    plt.tight_layout()
    st.pyplot(fig)

# Streamlit App Functions

def view_stocks():
    """View all stock entries in a table with comparison charts."""
    st.header("📊 All Stock Entries")

    stocks = get_all_stocks()

    if not stocks:
        st.info("No stock entries found. Click on 'Add Stock' in the sidebar to create a new entry.")
        return

    # Convert stock data to DataFrame
    df = pd.DataFrame(stocks)

    # Calculate additional metrics using pandas and numpy
    metrics_df = df.apply(lambda x: calculate_metrics(
        x['total_shares'], x['buy_price'], x['risk_ratio'], x['reward_ratio'], x['sell_strategy']
    ), axis=1)

    # Concatenate original data and calculated metrics
    combined_df = pd.concat([df, metrics_df], axis=1)

    # Select a stock based on stock symbol
    stock_symbols = combined_df['stock_symbol'].tolist()
    selected_symbol = st.selectbox("Select a Stock Symbol to View Details", options=stock_symbols)

    if selected_symbol:
        selected_stock = combined_df[combined_df['stock_symbol'] == selected_symbol].iloc[0]

        # Display inputs first
        st.subheader(f"🔍 Details for {selected_symbol}")
        with st.expander("📋 Input Details"):
            st.markdown(f"**Stock Symbol:** {selected_stock['stock_symbol']}")
            st.markdown(f"**Total Shares:** {selected_stock['total_shares']}")
            st.markdown(f"**Buy Price ($):** ${selected_stock['buy_price']:.2f}")
            st.markdown(f"**Risk Ratio (%):** {selected_stock['risk_ratio']:.2f}%")
            st.markdown(f"**Reward Ratio (%):** {selected_stock['reward_ratio']:.2f}%")
            st.markdown(f"**Sell Strategy:** {selected_stock['sell_strategy']}")
            st.markdown(f"**Sell Price ($):** ${selected_stock['sell_price']:.2f}" if selected_stock['sell_price'] else "N/A")

        # Display outputs next
        with st.expander("📈 Calculated Metrics"):
            st.markdown(f"**Total Investment ($):** ${selected_stock['Total Investment ($)']:.2f}")
            st.markdown(f"**Risk Amount ($):** ${selected_stock['Risk Amount ($)']:.2f}")
            st.markdown(f"**Reward Amount ($):** ${selected_stock['Reward Amount ($)']:.2f}")
            st.markdown(f"**Stop-Loss Price ($):** ${selected_stock['Stop-Loss Price ($)']:.2f}")
            st.markdown(f"**Take-Profit Price ($):** ${selected_stock['Take-Profit Price ($)']:.2f}")
            st.markdown(f"**Adjusted Sell Price ($):** ${selected_stock['Adjusted Sell Price ($)']:.2f}")

        # Plot the detailed metrics for the selected stock
        st.subheader("📊 Financial Metrics Chart for Selected Stock")
        metrics = ['Total Investment ($)', 'Risk Amount ($)', 'Reward Amount ($)', 'Stop-Loss Price ($)', 'Take-Profit Price ($)', 'Adjusted Sell Price ($)']
        metric_values = [selected_stock[metric] for metric in metrics]

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.barh(metrics, metric_values, color='lightblue')
        ax.set_xlabel('Amount ($)')
        ax.set_title(f'Financial Metrics for {selected_symbol}')
        plt.tight_layout()
        st.pyplot(fig)

    # Comparison Chart for All Stocks
    st.subheader("📈 Comparison of Key Metrics Across All Stocks")
    comparison_metrics = ['Total Investment ($)', 'Risk Amount ($)', 'Reward Amount ($)', 'Stop-Loss Price ($)', 'Take-Profit Price ($)', 'Adjusted Sell Price ($)']
    plot_comparison_chart(combined_df, comparison_metrics, "Key Financial Metrics Comparison")

def add_stock():
    """Add a new stock entry via a form."""
    st.header("➕ Add New Stock Entry")

    with st.form("add_stock_form"):
        stock_symbol = st.text_input("Stock Symbol", "").upper()
        total_shares = st.number_input("Total Shares", min_value=1, value=1, step=1)
        buy_price = st.number_input("Buy Price ($)", min_value=0.01, value=0.01, step=0.01)
        risk_ratio = st.number_input("Risk Ratio (%)", min_value=0.00, max_value=100.00, value=5.00, step=0.01)
        reward_ratio = st.number_input("Reward Ratio (%)", min_value=0.00, max_value=100.00, value=10.00, step=0.01)
        sell_strategy = st.selectbox("Sell Strategy", ["Risk-Based", "Reward-Based"])
        sell_price = st.number_input("Sell Price ($) [Optional]", min_value=0.00, value=0.00, step=0.01)
        submit_button = st.form_submit_button("Add Stock")

    if submit_button:
        # Input Validation
        if not stock_symbol:
            st.error("Stock Symbol cannot be empty.")
            return
        if buy_price < 0.01:
            st.error("Buy Price must be at least $0.01.")
            return

        # Determine sell price value
        sell_price_value = sell_price if sell_price > 0 else None

        # Prepare entry dictionary
        entry = {
            'stock_symbol': stock_symbol,
            'total_shares': int(total_shares),
            'buy_price': float(buy_price),
            'risk_ratio': float(risk_ratio),
            'reward_ratio': float(reward_ratio),
            'sell_strategy': sell_strategy,
            'sell_price': float(sell_price_value) if sell_price_value else None
        }

        # Add entry to database
        success = add_stock_entry(entry)
        if success:
            st.success("Stock entry added successfully!")
        else:
            st.error("Failed to add stock entry.")

def edit_stock():
    """Edit an existing stock entry."""
    st.header("✏️ Edit Existing Stock Entry")

    stocks = get_all_stocks()

    if not stocks:
        st.info("No stock entries found to edit.")
        return

    # Select stock to edit based on stock symbol
    stock_symbols = [stock['stock_symbol'] for stock in stocks]
    selected_symbol = st.selectbox("Select Stock Symbol to Edit", options=stock_symbols)

    if selected_symbol:
        stock = next((s for s in stocks if s['stock_symbol'] == selected_symbol), None)

        if stock:
            with st.form("edit_stock_form"):
                stock_symbol = st.text_input("Stock Symbol", stock['stock_symbol']).upper()
                total_shares = st.number_input("Total Shares", min_value=1, value=stock['total_shares'], step=1)
                buy_price = st.number_input("Buy Price ($)", min_value=0.01, value=stock['buy_price'], step=0.01)
                risk_ratio = st.number_input("Risk Ratio (%)", min_value=0.00, max_value=100.00, value=stock['risk_ratio'], step=0.01)
                reward_ratio = st.number_input("Reward Ratio (%)", min_value=0.00, max_value=100.00, value=stock['reward_ratio'], step=0.01)
                sell_strategy = st.selectbox("Sell Strategy", ["Risk-Based", "Reward-Based"], index=0 if stock['sell_strategy'] == "Risk-Based" else 1)
                sell_price = st.number_input("Sell Price ($) [Optional]", min_value=0.00, value=stock['sell_price'] if stock['sell_price'] else 0.00, step=0.01)
                submit_button = st.form_submit_button("Update Stock")

            if submit_button:
                # Input Validation
                if not stock_symbol:
                    st.error("Stock Symbol cannot be empty.")
                    return
                if buy_price < 0.01:
                    st.error("Buy Price must be at least $0.01.")
                    return

                # Determine sell price value
                sell_price_value = sell_price if sell_price > 0 else None

                # Prepare updated entry dictionary
                updated_entry = {
                    'stock_symbol': stock_symbol,
                    'total_shares': int(total_shares),
                    'buy_price': float(buy_price),
                    'risk_ratio': float(risk_ratio),
                    'reward_ratio': float(reward_ratio),
                    'sell_strategy': sell_strategy,
                    'sell_price': float(sell_price_value) if sell_price_value else None
                }

                # Update entry in database
                success = update_stock_entry(stock['id'], updated_entry)
                if success:
                    st.success("Stock entry updated successfully!")
                else:
                    st.error("Failed to update stock entry.")

def delete_stock():
    """Delete an existing stock entry."""
    st.header("🗑️ Delete Stock Entry")

    stocks = get_all_stocks()

    if not stocks:
        st.info("No stock entries found to delete.")
        return

    # Select stock to delete based on stock symbol
    stock_symbols = [stock['stock_symbol'] for stock in stocks]
    selected_symbol = st.selectbox("Select Stock Symbol to Delete", options=stock_symbols)

    if selected_symbol:
        stock = next((s for s in stocks if s['stock_symbol'] == selected_symbol), None)

        if stock:
            st.warning(f"Are you sure you want to delete **{stock['stock_symbol']}** with **{stock['total_shares']}** shares?")
            if st.button("Delete Stock"):
                success = delete_stock_entry(stock['id'])
                if success:
                    st.success("Stock entry deleted successfully!")
                else:
                    st.error("Failed to delete stock entry.")

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="Stock Trading Manager", layout="wide")
    st.title("📈 Stock Trading Manager")

    # Initialize the database
    init_db()

    # Sidebar Navigation
    menu = ["View Stocks", "Add Stock", "Edit Stock", "Delete Stock"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "View Stocks":
        view_stocks()
    elif choice == "Add Stock":
        add_stock()
    elif choice == "Edit Stock":
        edit_stock()
    elif choice == "Delete Stock":
        delete_stock()

if __name__ == "__main__":
    main()

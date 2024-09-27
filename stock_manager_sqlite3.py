import streamlit as st
import pandas as pd
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
                stock_symbol TEXT NOT NULL,
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

# Calculation Function

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

    return {
        'Total Investment ($)': round(total_investment, 2),
        'Risk Amount ($)': round(risk_amount, 2),
        'Reward Amount ($)': round(reward_amount, 2),
        'Stop-Loss Price ($)': round(stop_loss_price, 2),
        'Take-Profit Price ($)': round(take_profit_price, 2),
        'Adjusted Sell Price ($)': round(adjusted_sell_price, 2)
    }

# Streamlit App Functions

def view_stocks():
    """View all stock entries in a table."""
    st.header("📊 All Stock Entries")

    stocks = get_all_stocks()

    if not stocks:
        st.info("No stock entries found. Click on 'Add Stock' in the sidebar to create a new entry.")
        return

    # Prepare table data
    table_data = []
    headers = [
        'ID', 'Stock Symbol', 'Total Shares', 'Buy Price ($)', 'Risk Ratio (%)',
        'Reward Ratio (%)', 'Sell Strategy', 'Sell Price ($)',
        'Total Investment ($)', 'Risk Amount ($)', 'Reward Amount ($)',
        'Stop-Loss Price ($)', 'Take-Profit Price ($)', 'Adjusted Sell Price ($)'
    ]

    for stock in stocks:
        metrics = calculate_metrics(
            stock['total_shares'],
            stock['buy_price'],
            stock['risk_ratio'],
            stock['reward_ratio'],
            stock['sell_strategy']
        )
        row = [
            stock['id'],
            stock['stock_symbol'],
            stock['total_shares'],
            stock['buy_price'],
            stock['risk_ratio'],
            stock['reward_ratio'],
            stock['sell_strategy'],
            stock['sell_price'],
            metrics['Total Investment ($)'],
            metrics['Risk Amount ($)'],
            metrics['Reward Amount ($)'],
            metrics['Stop-Loss Price ($)'],
            metrics['Take-Profit Price ($)'],
            metrics['Adjusted Sell Price ($)']
        ]
        table_data.append(row)

    # Convert table data to a DataFrame
    df = pd.DataFrame(table_data, columns=headers)

    # Ensure all columns are of compatible data types for Arrow serialization
    df = df.astype(str)

    # Display the DataFrame in Streamlit
    st.dataframe(df)

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

if __name__ == "__main__":
    main()

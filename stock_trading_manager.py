import streamlit as st
import json
import os
import pandas as pd

# Constants
DATA_FILE = 'stocks.json'

# Helper Classes and Functions

class StockEntry:
    def __init__(self, stock_symbol, total_shares, buy_price, risk_ratio,
                 reward_ratio, sell_strategy, sell_price=None):
        self.stock_symbol = stock_symbol.upper()
        self.total_shares = total_shares
        self.buy_price = buy_price
        self.risk_ratio = risk_ratio
        self.reward_ratio = reward_ratio
        self.sell_strategy = sell_strategy  # "Risk-Based" or "Reward-Based"
        self.sell_price = sell_price  # Optional: Can be calculated

    def to_dict(self):
        return {
            'stock_symbol': self.stock_symbol,
            'total_shares': self.total_shares,
            'buy_price': self.buy_price,
            'risk_ratio': self.risk_ratio,
            'reward_ratio': self.reward_ratio,
            'sell_strategy': self.sell_strategy,
            'sell_price': self.sell_price
        }

    @staticmethod
    def from_dict(data):
        # Provide default values if fields are missing
        return StockEntry(
            stock_symbol=data.get('stock_symbol', 'UNKNOWN'),
            total_shares=data.get('total_shares', 0),
            buy_price=data.get('buy_price', 0.0),
            risk_ratio=data.get('risk_ratio', 0.0),
            reward_ratio=data.get('reward_ratio', 0.0),
            sell_strategy=data.get('sell_strategy', 'Reward-Based'),
            sell_price=data.get('sell_price', None)
        )

    def calculate_metrics(self):
        total_investment = self.total_shares * self.buy_price
        risk_amount = self.buy_price * (self.risk_ratio / 100)
        reward_amount = self.buy_price * (self.reward_ratio / 100)
        stop_loss_price = self.buy_price - risk_amount
        take_profit_price = self.buy_price + reward_amount

        if self.sell_strategy == "Risk-Based":
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

def read_json():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
    with open(DATA_FILE, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
    return data

def write_json(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error writing to JSON: {e}")
        return False

def get_stock_entries():
    data = read_json()
    return [StockEntry.from_dict(entry) for entry in data]

def save_stock_entries(entries):
    data = [entry.to_dict() for entry in entries]
    return write_json(data)

def add_stock_entry(entry, entries):
    entries.append(entry)
    return save_stock_entries(entries)

def update_stock_entry(index, updated_entry, entries):
    if 0 <= index < len(entries):
        entries[index] = updated_entry
        return save_stock_entries(entries)
    else:
        st.error("Invalid stock entry index.")
        return False

def delete_stock_entry(index, entries):
    if 0 <= index < len(entries):
        del entries[index]
        return save_stock_entries(entries)
    else:
        st.error("Invalid stock entry index.")
        return False

# Streamlit App

def main():
    st.set_page_config(page_title="Stock Trading Manager", layout="wide")
    st.title("📈 Stock Trading Manager")

    # Initialize session state
    if 'entries' not in st.session_state:
        st.session_state.entries = get_stock_entries()

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose Action", ["View Stocks", "Add Stock", "Edit Stock", "Delete Stock"])

    if app_mode == "View Stocks":
        view_stocks()
    elif app_mode == "Add Stock":
        add_stock()
    elif app_mode == "Edit Stock":
        edit_stock()
    elif app_mode == "Delete Stock":
        delete_stock()

def view_stocks():
    st.header("📊 All Stock Entries")

    if not st.session_state.entries:
        st.info("No stock entries found. Click on 'Add Stock' in the sidebar to create a new entry.")
        return

    # Prepare DataFrame
    data = []
    for entry in st.session_state.entries:
        metrics = entry.calculate_metrics()
        data.append({
            'Stock Symbol': entry.stock_symbol,
            'Total Shares': entry.total_shares,
            'Buy Price ($)': entry.buy_price,
            'Risk Ratio (%)': entry.risk_ratio,
            'Reward Ratio (%)': entry.reward_ratio,
            'Sell Strategy': entry.sell_strategy,
            'Total Investment ($)': metrics['Total Investment ($)'],
            'Risk Amount ($)': metrics['Risk Amount ($)'],
            'Reward Amount ($)': metrics['Reward Amount ($)'],
            'Stop-Loss Price ($)': metrics['Stop-Loss Price ($)'],
            'Take-Profit Price ($)': metrics['Take-Profit Price ($)'],
            'Adjusted Sell Price ($)': metrics['Adjusted Sell Price ($)']
        })

    df = pd.DataFrame(data)
    st.dataframe(df.style.format({
        'Buy Price ($)': "{:.2f}",
        'Risk Ratio (%)': "{:.2f}",
        'Reward Ratio (%)': "{:.2f}",
        'Total Investment ($)': "{:.2f}",
        'Risk Amount ($)': "{:.2f}",
        'Reward Amount ($)': "{:.2f}",
        'Stop-Loss Price ($)': "{:.2f}",
        'Take-Profit Price ($)': "{:.2f}",
        'Adjusted Sell Price ($)': "{:.2f}"
    }), height=600)

def add_stock():
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
        if not stock_symbol:
            st.error("Stock Symbol cannot be empty.")
            return
        if buy_price < 0.01:
            st.error("Buy Price must be at least $0.01.")
            return

        sell_price_value = sell_price if sell_price > 0 else None

        new_entry = StockEntry(
            stock_symbol=stock_symbol,
            total_shares=int(total_shares),
            buy_price=float(buy_price),
            risk_ratio=float(risk_ratio),
            reward_ratio=float(reward_ratio),
            sell_strategy=sell_strategy,
            sell_price=sell_price_value
        )

        success = add_stock_entry(new_entry, st.session_state.entries)
        if success:
            st.success("Stock entry added successfully!")
            st.session_state.entries = get_stock_entries()
        else:
            st.error("Failed to add stock entry.")

def edit_stock():
    st.header("✏️ Edit Existing Stock Entry")

    if not st.session_state.entries:
        st.info("No stock entries found to edit.")
        return

    # Select stock to edit
    stock_options = [f"{i+1}. {entry.stock_symbol} - {entry.total_shares} shares" 
                    for i, entry in enumerate(st.session_state.entries)]
    selected_stock = st.selectbox("Select Stock to Edit", options=stock_options)

    if selected_stock:
        index = stock_options.index(selected_stock)
        entry = st.session_state.entries[index]

        with st.form("edit_stock_form"):
            stock_symbol = st.text_input("Stock Symbol", entry.stock_symbol).upper()
            total_shares = st.number_input("Total Shares", min_value=1, value=entry.total_shares, step=1)
            buy_price = st.number_input("Buy Price ($)", min_value=0.01, value=entry.buy_price, step=0.01)
            risk_ratio = st.number_input("Risk Ratio (%)", min_value=0.00, max_value=100.00, value=entry.risk_ratio, step=0.01)
            reward_ratio = st.number_input("Reward Ratio (%)", min_value=0.00, max_value=100.00, value=entry.reward_ratio, step=0.01)
            sell_strategy = st.selectbox("Sell Strategy", ["Risk-Based", "Reward-Based"], index=0 if entry.sell_strategy == "Risk-Based" else 1)
            sell_price = st.number_input("Sell Price ($) [Optional]", min_value=0.00, value=entry.sell_price if entry.sell_price else 0.00, step=0.01)
            submit_button = st.form_submit_button("Update Stock")

        if submit_button:
            if not stock_symbol:
                st.error("Stock Symbol cannot be empty.")
                return
            if buy_price < 0.01:
                st.error("Buy Price must be at least $0.01.")
                return

            sell_price_value = sell_price if sell_price > 0 else None

            updated_entry = StockEntry(
                stock_symbol=stock_symbol,
                total_shares=int(total_shares),
                buy_price=float(buy_price),
                risk_ratio=float(risk_ratio),
                reward_ratio=float(reward_ratio),
                sell_strategy=sell_strategy,
                sell_price=sell_price_value
            )

            success = update_stock_entry(index, updated_entry, st.session_state.entries)
            if success:
                st.success("Stock entry updated successfully!")
                st.session_state.entries = get_stock_entries()
            else:
                st.error("Failed to update stock entry.")

def delete_stock():
    st.header("🗑️ Delete Stock Entry")

    if not st.session_state.entries:
        st.info("No stock entries found to delete.")
        return

    # Select stock to delete
    stock_options = [f"{i+1}. {entry.stock_symbol} - {entry.total_shares} shares" 
                    for i, entry in enumerate(st.session_state.entries)]
    selected_stock = st.selectbox("Select Stock to Delete", options=stock_options)

    if selected_stock:
        index = stock_options.index(selected_stock)
        entry = st.session_state.entries[index]
        st.warning(f"Are you sure you want to delete **{entry.stock_symbol}** with **{entry.total_shares}** shares?")

        if st.button("Delete Stock"):
            success = delete_stock_entry(index, st.session_state.entries)
            if success:
                st.success("Stock entry deleted successfully!")
                st.session_state.entries = get_stock_entries()
                st.experimental_rerun()
            else:
                st.error("Failed to delete stock entry.")

if __name__ == '__main__':
    main()

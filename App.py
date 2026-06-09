import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# =====================================================================
# --- 0. Basic page configuration ---
# =====================================================================
st.set_page_config(page_title="ShopEasy Backend data analysis dashboard", layout="wide")
st.title("🛍️ ShopEasy Sales & Inventory Dashboard")

# =====================================================================
# --- 1. Core data loading (Use st.cache_data to lock the data source) ---
# =====================================================================
@st.cache_data
def load_essential_data():
    sales = pd.read_csv("sales_data.csv")
    inventory = pd.read_csv("inventory_data.csv")
    #
    # Ensure the date format is correct.
    sales['date_of_sale'] = pd.to_datetime(sales['date_of_sale'])
    return sales, inventory

try:
    df_sales, df_inventory = load_essential_data()
except FileNotFoundError:
    st.error(
"❌ Error: CSV data file not found! Please ensure that sales_data.csv and inventory_data.csv exist in the current directory.")
    st.stop()

# =====================================================================
# --- 2. Sidebar Filter Console ---
# =====================================================================
st.sidebar.header("🔍 Data filtering console")

# Category filtering
all_categories = ["all"] + list(df_sales['category'].unique())
selected_category = st.sidebar.selectbox("Select product category", all_categories)

# Date range filter
min_date = df_sales['date_of_sale'].min().date()
max_date = df_sales['date_of_sale'].max().date()
selected_date_range = st.sidebar.date_input(
    "Select sales date range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# --- Perform data filtering ---
filtered_sales = df_sales.copy()

if selected_category != "all":
    filtered_sales = filtered_sales[filtered_sales['category'] == selected_category]

if isinstance(selected_date_range, (list, tuple)) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
    filtered_sales = filtered_sales[
        (filtered_sales['date_of_sale'].dt.date >= start_date) &
        (filtered_sales['date_of_sale'].dt.date <= end_date)
    ]

# =====================================================================
# --- 3.
# Core Business Indicator Card ---
# =====================================================================
st.subheader("📈 core business indicators")

if not filtered_sales.empty:
    total_revenue = (filtered_sales['quantity_sold'] * filtered_sales['unit_price']).sum()
    total_units_sold = filtered_sales['quantity_sold'].sum()
    average_selling_price = total_revenue / total_units_sold
else:
    total_revenue, total_units_sold, average_selling_price = 0.0, 0, 0.0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Revenue", value=f"RM {total_revenue:,.2f}")
with col2:
    st.metric(label="Total Units Sold", value=f"{total_units_sold:,} 件")
with col3:
    st.metric(label="Average Selling Price", value=f"RM {average_selling_price:,.2f}")

st.markdown("---")

# =====================================================================
# --- 4. Sales data flow table ---
# =====================================================================
st.subheader("📊 Sales data flow (filtered)")
st.dataframe(filtered_sales, use_container_width=True)
st.markdown("---")

# =====================================================================
# --- 5. Data visualization dashboard ---
# =====================================================================
st.subheader("📊 Sales data visualization dashboard")

if not filtered_sales.empty:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### 🛍️ Comparison of total revenue by category")
        temp_sales = filtered_sales.copy()
        temp_sales['revenue'] = temp_sales['quantity_sold'] * temp_sales['unit_price']
        category_revenue = temp_sales.groupby('category')['revenue'].sum().reset_index()

        fig1, ax1 = plt.subplots(figsize=(6, 4))
        sns.barplot(data=category_revenue, x='category', y='revenue', palette='Blues_r', ax=ax1)
        ax1.set_title("Total Revenue by Product Category")
        ax1.set_xlabel("Category")
        ax1.set_ylabel("Total Revenue (RM)")
        plt.xticks(rotation=15)
        plt.tight_layout()
        st.pyplot(fig1)

    with chart_col2:
        st.markdown("#### 📈 Sales trend over time")
        daily_revenue = temp_sales.groupby('date_of_sale')['revenue'].sum().reset_index()
        daily_revenue = daily_revenue.sort_values('date_of_sale')

        fig2, ax2 = plt.subplots(figsize=(6, 4))
        sns.lineplot(data=daily_revenue, x='date_of_sale', y='revenue', marker='o', color='g', ax=ax2)
        ax2.set_title("Sales Revenue Trend Over Time")
        ax2.set_xlabel("Date of Sale")
        ax2.set_ylabel("Daily Revenue (RM)")
        plt.xticks(rotation=30)
        plt.tight_layout()
        st.pyplot(fig2)

    st.markdown("#### 🎯 In-depth business analysis: Distribution relationship between unit price and sales volume of goods (scatter plot)")
    fig3, ax3 = plt.subplots(figsize=(10, 3.5))
    sns.scatterplot(data=filtered_sales, x='unit_price', y='quantity_sold', hue='category', style='category', s=100, ax=ax3)
    ax3.set_title("Product Price vs. Quantity Sold Analysis")
    ax3.set_xlabel("Unit Price (RM)")
    ax3.set_ylabel("Quantity Sold (Units)")
    ax3.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig3)
else:
    st.warning("There is no sales data under the current filter conditions, so a chart cannot be generated.。")

st.markdown("---")

# =====================================================================
# --- 6.
# Inventory Management and Risk Warning System (Fixed slider locking issue) ---
# =====================================================================
st.subheader("🚨 ShopEasy Inventory Management and Risk Early Warning System")

# 这里的 key="stock_slider" 能够强行让 Streamlit 在会话中记住滑块的位置，防止滑块锁死
stock_threshold = st.slider(
    " Low Stock Threshold Target:",
    min_value=5,
    max_value=50,
    value=20,
    step=1,
    key="stock_slider"
)

#
# Converting to a dictionary list is a key point in functional programming.
inventory_list = df_inventory.to_dict(orient='records')
low_stock_items = list(filter(lambda item: item['stock_quantity'] < stock_threshold, inventory_list))

if low_stock_items:
    st.warning(f"⚠️ Core warning: A warning has been detected that there is currently **{len(low_stock_items)}** Product inventory is below your set safety line（{stock_threshold} pieces），Please arrange for replenishment in a timely manner.！")
    df_low_stock = pd.DataFrame(low_stock_items)
    st.markdown("**🚨 List of Items in Short Supply：**")
    st.dataframe(df_low_stock[['product_name', 'category', 'stock_quantity']], use_container_width=True)
else:
    st.success(f"🎉 Good condition: All product inventory is currently at a safe level.（{stock_threshold} (Items) or more!")

st.markdown("#### 📋 Complete inventory status overview")

def highlight_low_stock(row, threshold):
    if row['stock_quantity'] < threshold:
        return ['background-color: #ffcccc'] * len(row)
    return [''] * len(row)

styled_inventory = df_inventory.style.apply(
    highlight_low_stock,
    axis=1,
    threshold=stock_threshold
)

st.dataframe(styled_inventory, use_container_width=True)
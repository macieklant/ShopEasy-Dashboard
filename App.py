import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# =====================================================================
# --- 0. 页面基础配置 ---
# =====================================================================
st.set_page_config(page_title="ShopEasy 后台数据分析看板", layout="wide")
st.title("🛍️ ShopEasy Sales & Inventory Dashboard")

# =====================================================================
# --- 1. 核心数据加载 (使用 st.cache_data 锁定数据源) ---
# =====================================================================
@st.cache_data
def load_essential_data():
    sales = pd.read_csv("sales_data.csv")
    inventory = pd.read_csv("inventory_data.csv")
    # 确保日期格式正确
    sales['date_of_sale'] = pd.to_datetime(sales['date_of_sale'])
    return sales, inventory

try:
    df_sales, df_inventory = load_essential_data()
except FileNotFoundError:
    st.error("❌ 错误：未找到 CSV 数据文件！请确保 sales_data.csv 和 inventory_data.csv 存在于当前目录下。")
    st.stop()

# =====================================================================
# --- 2. 侧边栏过滤器控制台 ---
# =====================================================================
st.sidebar.header("🔍 数据筛选控制台")

# 品类筛选
all_categories = ["全部"] + list(df_sales['category'].unique())
selected_category = st.sidebar.selectbox("选择商品品类", all_categories)

# 日期范围筛选
min_date = df_sales['date_of_sale'].min().date()
max_date = df_sales['date_of_sale'].max().date()
selected_date_range = st.sidebar.date_input(
    "选择销售日期范围",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# --- 执行数据过滤 ---
filtered_sales = df_sales.copy()

if selected_category != "全部":
    filtered_sales = filtered_sales[filtered_sales['category'] == selected_category]

if isinstance(selected_date_range, (list, tuple)) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
    filtered_sales = filtered_sales[
        (filtered_sales['date_of_sale'].dt.date >= start_date) &
        (filtered_sales['date_of_sale'].dt.date <= end_date)
    ]

# =====================================================================
# --- 3. 核心业务指标卡片 ---
# =====================================================================
st.subheader("📈 核心业务指标")

if not filtered_sales.empty:
    total_revenue = (filtered_sales['quantity_sold'] * filtered_sales['unit_price']).sum()
    total_units_sold = filtered_sales['quantity_sold'].sum()
    average_selling_price = total_revenue / total_units_sold
else:
    total_revenue, total_units_sold, average_selling_price = 0.0, 0, 0.0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="总收入 (Total Revenue)", value=f"RM {total_revenue:,.2f}")
with col2:
    st.metric(label="总销量 (Total Units Sold)", value=f"{total_units_sold:,} 件")
with col3:
    st.metric(label="平均售价 (Average Selling Price)", value=f"RM {average_selling_price:,.2f}")

st.markdown("---")

# =====================================================================
# --- 4. 销售数据流水表 ---
# =====================================================================
st.subheader("📊 销售数据流水（已过滤）")
st.dataframe(filtered_sales, use_container_width=True)
st.markdown("---")

# =====================================================================
# --- 5. 数据可视化看板 ---
# =====================================================================
st.subheader("📊 销售数据可视化看板")

if not filtered_sales.empty:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### 🛍️ 各品类总收入对比")
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
        st.markdown("#### 📈 销售额随时间趋势变化")
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

    st.markdown("#### 🎯 深度商业 analysis：商品单价与销量的分布关系（散点图）")
    fig3, ax3 = plt.subplots(figsize=(10, 3.5))
    sns.scatterplot(data=filtered_sales, x='unit_price', y='quantity_sold', hue='category', style='category', s=100, ax=ax3)
    ax3.set_title("Product Price vs. Quantity Sold Analysis")
    ax3.set_xlabel("Unit Price (RM)")
    ax3.set_ylabel("Quantity Sold (Units)")
    ax3.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig3)
else:
    st.warning("当前筛选条件下无销售数据，无法绘制图表。")

st.markdown("---")

# =====================================================================
# --- 6. 库存管理与风险预警系统 (修复滑块锁定问题) ---
# =====================================================================
st.subheader("🚨 ShopEasy 库存管理与风险预警系统")

# 这里的 key="stock_slider" 能够强行让 Streamlit 在会话中记住滑块的位置，防止滑块锁死
stock_threshold = st.slider(
    "请设定低库存报警阈值 (Low Stock Threshold Target):",
    min_value=5,
    max_value=50,
    value=20,
    step=1,
    key="stock_slider"
)

# 转换为字典列表以满足函数式编程考点
inventory_list = df_inventory.to_dict(orient='records')
low_stock_items = list(filter(lambda item: item['stock_quantity'] < stock_threshold, inventory_list))

if low_stock_items:
    st.warning(f"⚠️ 核心预警：检测到当前有 **{len(low_stock_items)}** 款商品库存低于您设定的安全线（{stock_threshold} 件），请及时安排补货！")
    df_low_stock = pd.DataFrame(low_stock_items)
    st.markdown("**🚨 告急商品清单：**")
    st.dataframe(df_low_stock[['product_name', 'category', 'stock_quantity']], use_container_width=True)
else:
    st.success(f"🎉 状态良好：目前所有商品库存均在安全线（{stock_threshold} 件）以上！")

st.markdown("#### 📋 完整库存状态一览表")

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
# bar_exchange_demo/app.py
import streamlit as st
from datetime import datetime, timedelta
from core import ExchangeState, Drink, User
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import font_manager
import polars as F
import os
import pandas as pd
C = F.col
import time, string

if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.exchange = ExchangeState()

exchange = st.session_state.exchange

if not st.session_state.initialized:
    st.title("🍻 初始化交易所系统")

    num_users = st.number_input("消费者数量", min_value=1, max_value=10, value=4)
    num_drinks = st.number_input("酒款数量", min_value=1, max_value=10, value=3)

    with st.form("init_form"):
        default_user_names = [f"user_{i}" for i in range(num_users)]
        default_drink_names = [f"啤酒{c}" for c in string.ascii_uppercase[:num_drinks]]

        st.write("🍺 酒款设置：")
        drink_prices = [st.number_input(f"{default_drink_names[i]} 初始价格", min_value=0.1, value=10.0)
                        for i in range(num_drinks)]

        submitted = st.form_submit_button("开始使用系统")
        if submitted:
            # 初始化
            for name in default_user_names:
                exchange.users.append(User(name))
            for name, price in zip(default_drink_names, drink_prices):
                exchange.drinks[name] = Drink(name, price)

            st.session_state.initialized = True
            st.rerun()

    st.stop()


# 常见的中文字体候选
st.write(os.path.exists('./fonts/simhei.ttf'))

font_path = './fonts/simhei.ttf'  # 字体文件路径
font_prop = font_manager.FontProperties(fname=font_path)
# plt.rcParams['font.family'] = font_prop.get_name()
# print("✅ 加载字体成功：", font_prop.get_name())  # 可打印出来检查

# font_path = os.path.join("fonts", "NotoSansSC-Regular.otf")
# if os.path.exists(font_path):
#     font_prop = font_manager.FontProperties(fname=font_path)
#     plt.rcParams['font.family'] = font_prop.get_name()
#     print("✅ 加载字体成功：", font_prop.get_name())  # 可打印出来检查
# else:
#     plt.rcParams['font.family'] = 'sans-serif'
#     print("❌ 字体文件未找到，使用默认字体")

# plt.rcParams['font.family'] = 'Microsoft YaHei'#'SimHei'        # 设置中文字体为黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

st.set_page_config(layout="wide")

# 初始化 session state
# if 'exchange' not in st.session_state:
#     st.session_state.exchange = ExchangeState()
# exchange = st.session_state.exchange

# auto_run = st.sidebar.checkbox("自动推进时间（每秒+1分钟）")
# refresh_button = st.sidebar.button("手动刷新图表")

# if 'last_auto_advance' not in st.session_state:
#     st.session_state.last_auto_advance = datetime.now()
# if auto_run:
#     now = datetime.now()
#     if (now - st.session_state.last_auto_advance).total_seconds() >= 1:
#         exchange.advance_time(minutes=1)
#         st.session_state.last_auto_advance = now
#         st.rerun()

# 时间控制
col_time1, col_time2 = st.sidebar.columns(2)
if col_time1.button(">>前进1分钟"): #<< 回退5分钟
    exchange.advance_time(minutes=1)
if col_time2.button(">>前进5分钟"):
    exchange.advance_time(minutes=5)
col_time3, col_time4 = st.sidebar.columns(2)
if col_time3.button(">>前进15分钟"):
    exchange.advance_time(minutes=15)
if col_time4.button(">>前进60分钟"):
    exchange.advance_time(minutes=60)
# 显示当前时间
st.sidebar.title("控制面板")
st.sidebar.write(f"当前时间：{exchange.current_time} 分钟") ##.strftime('%Y-%m-%d %H:%M:%S')



st.sidebar.markdown("---")

# 用户选择
selected_user = st.sidebar.selectbox("选择消费者", exchange.get_user_names())
selected_drink = st.sidebar.selectbox("选择酒款", exchange.get_drink_names())
qty = st.sidebar.slider("买卖数量", 1, 5, 1)

# 买卖操作
col_tr1, col_tr2 = st.sidebar.columns(2)
if col_tr1.button("买入"):
    exchange.buy(selected_user, selected_drink, qty)
if col_tr2.button("卖出"):
    exchange.sell(selected_user, selected_drink, qty)

if st.sidebar.button("喝一杯"):
    exchange.consume(selected_user, selected_drink)

# 撤销
if st.sidebar.button("撤销上一步"):
    exchange.undo_last()


# 展示每种酒价格走势
st.markdown("<h1 style='font-size:28px;'>酒吧交易所 Demo</h1>", unsafe_allow_html=True)

prices = exchange.get_all_drink_prices()
for user in exchange.users:
    user.coupon_value = user.get_coupon_value(prices)
    user.net_asset = -user.total_spent + user.coupon_value + user.stored_value
    # total_coupon_value += value
    # st.write(f"{user.name} 的酒券总价值: ￥{value:.2f}")
exchange.total_coupon_count = exchange.get_total_coupon_count()
exchange.total_coupon_value = exchange.get_total_coupon_value()
exchange.total_stored_value = exchange.get_total_stored_value()

# st.header("📊 交易所财务概况")
summary_df = pd.DataFrame([{
    "总营收（充值）": f"￥{exchange.total_recharge:.2f}",
    "在外酒券张数": exchange.total_coupon_count,
    "在外酒券总价值": f"￥{exchange.total_coupon_value:.2f}",
    "在外储值总金额": f"￥{exchange.total_stored_value:.2f}",
    "净利润": f"￥{exchange.get_net_revenue():.2f}"
}])
st.markdown(f"<p style='font-size:18px;'>交易所财务概况", unsafe_allow_html=True)
st.table(summary_df)


# 展示用户持仓
# st.markdown("<h2 style='font-size:22px;'>用户持仓</h2>", unsafe_allow_html=True)
rows = []
for user in exchange.users:
    prices = exchange.get_all_drink_prices()
    rows.append({
        "总花费": f"￥{user.total_spent:.2f}",
        "当前酒券张数": user.coupons,
        "当前酒券价值": f"￥{user.get_coupon_value(prices):.2f}",
        "已兑换酒券数量": user.coupons_redeemed,
        "储值金额": f"￥{user.stored_value:.2f}",
        "净资产": f"￥{user.get_net_asset(prices):.2f}"
    })
user_summary_df = pd.DataFrame(rows)
st.markdown(f"<p style='font-size:16px;'> 👤 所有用户概况 ", unsafe_allow_html=True) #{user.name}
st.dataframe(user_summary_df, use_container_width=True)


# should_draw = not auto_run or refresh_button
for drink_name in exchange.get_drink_names():
    st.markdown(f"<h3 style='font-size:20px;'>{drink_name} 当前价格：￥{exchange.get_price(drink_name):.2f}</h3>", unsafe_allow_html=True)

    df = exchange.get_trade_df(drink_name)  # 假设此方法返回包含 time, price, net_qty 的 DataFrame
    # print(df)
    if df.is_empty():
        st.write("暂无交易记录")
        continue
    # 筛选掉无交易的items
    df_trades = df.filter(C('net_qty')!=0)
    # 保留每个时间最后一笔交易价格和交易总量
    # print(df)
    df_by_time = df.group_by("time",maintain_order=True).agg(
        last_price = C('price').last(),
        net_qty_sum = C("net_qty").sum()
    )

    fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=False, gridspec_kw={'height_ratios': [1, 1, 1]})
    # if should_draw:
    # 1. 酒价 vs 交易次数
    axes[0].plot(range(1, len(df_trades)+1),df_trades['price'], marker='o', linestyle='-')
    # axes[0].set_xlabel("交易次数")
    axes[0].set_ylabel("酒价",fontproperties=font_prop)
    axes[0].set_title(f"{drink_name} 价格 vs 交易次数",fontproperties=font_prop)
    axes[0].set_xlim([-1, max(len(df_trades),12) + 2])
    axes[0].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # 2. 酒价 vs 时间
    axes[1].plot(df_by_time['time'], df_by_time['last_price'], marker='o', linestyle='-')
    axes[1].set_ylabel("酒价",fontproperties=font_prop)
    axes[1].set_xlim([-1, max(df_by_time['time'].max(),60) + 5])
    axes[1].set_title(f"{drink_name} 价格 vs 时间(分钟)",fontproperties=font_prop)

    # 3. 净交易量柱状图
    colors = ['red' if v > 0 else 'green' for v in df_by_time['net_qty_sum']]
    axes[2].bar(df_by_time['time'], df_by_time['net_qty_sum'], color=colors, width=1)# 
    axes[2].set_xlim([-1, max(df_by_time['time'].max(),60) + 5])
    axes[2].set_ylabel("净买卖量",fontproperties=font_prop)
    axes[2].set_xlabel("时间(分钟)",fontproperties=font_prop)
    axes[2].set_title("净买卖量 vs 时间(分钟)",fontproperties=font_prop)

    plt.tight_layout()
    st.pyplot(fig)




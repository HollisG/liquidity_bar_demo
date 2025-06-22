# bar_exchange_demo/app.py
import streamlit as st
from datetime import datetime, timedelta
from core import ExchangeState
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'SimHei'        # 设置中文字体为黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

st.set_page_config(layout="wide")

# 初始化 session state
if 'exchange' not in st.session_state:
    st.session_state.exchange = ExchangeState()
# st.write("✅ 页面加载成功")
exchange = st.session_state.exchange

# 显示当前时间
st.sidebar.title("控制面板")
st.sidebar.write(f"当前时间：{exchange.current_time.strftime('%Y-%m-%d %H:%M:%S')}")

# 时间控制
col_time1, col_time2 = st.sidebar.columns(2)
if col_time1.button("<< 回退5分钟"):
    exchange.rewind_time(minutes=5)
if col_time2.button(">> 前进5分钟"):
    exchange.advance_time(minutes=5)

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

st.sidebar.markdown("---")

# 展示每种酒价格走势
st.markdown("<h1 style='font-size:28px;'>酒吧交易所 Demo</h1>", unsafe_allow_html=True)

st.markdown(f"<p style='font-size:18px;'>净营收额：￥{exchange.revenue:.2f}</p>", unsafe_allow_html=True)

for drink_name in exchange.get_drink_names():
    st.markdown(f"<h3 style='font-size:20px;'>{drink_name} 当前价格：￥{exchange.get_price(drink_name):.2f}</h3>", unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(10,3))
    history = exchange.get_price_history(drink_name)
    ax.plot(history)
    ax.set_title(f"价格历史：{drink_name}")
    st.pyplot(fig)

# 展示用户持仓
st.markdown("<h2 style='font-size:22px;'>用户持仓</h2>", unsafe_allow_html=True)
for user in exchange.users:
    st.markdown(f"<h4 style='font-size:18px;'>{user.name}</h4>", unsafe_allow_html=True)
    st.write(user.holdings)
    st.write(f"交易记录：{user.trades[-5:]}")

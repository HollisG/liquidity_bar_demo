from datetime import datetime, timedelta
import copy
import pandas as pd
import numpy as np
import polars as F
C = F.col

class Drink:
    def __init__(self, name, init_price, base_price, halflife, price_impulse):
        self.name = name
        self.price = init_price
        self.base_price = base_price
        self.halflife = halflife
        self.price_history = [init_price]
        self.price_impulse = price_impulse

    def update_price(self, delta):
        self.price = max(0.01, self.price + delta)
        self.price_history.append(self.price)

    def mean_revert(self, minute):
        decay_factor = np.exp(-np.log(2) * minute / self.halflife)
        self.update_price(decay_factor * (self.base_price - self.price))


class User:
    def __init__(self, name):
        self.name = name
        self.holdings = {}  # {drink_name: qty}
        self.trades = []
        self.total_spent = 0.0  #总花费
        self.coupons = 0            # 当前持有酒券总张数
        self.coupon_value = 0            # 当前持有酒券总价值
        self.coupons_redeemed = 0   # 已兑换酒券
        self.stored_value = 0.0     # 储值金额
        self.net_asset = 0.0  # 净资产

    def get_coupon_value(self, price_map):
        return sum(qty * price_map.get(name, 0.0) for name, qty in self.holdings.items())

    def get_net_asset(self, price_map):
        return self.get_coupon_value(price_map) + self.stored_value - self.total_spent

    def get_coupon_count(self):
        return sum(self.holdings.values())

    def buy(self, drink_name, qty, price_per_unit):
        # self.holdings[drink_name] = self.holdings.get(drink_name, 0) + qty
        # total = price_per_unit * qty
        # self.trades.append(("buy", drink_name, qty, total))
        
        self.holdings[drink_name] = self.holdings.get(drink_name, 0) + qty
        total = price_per_unit * qty
        if self.stored_value >= total:
            self.stored_value -= total
            actual_spent = 0.0
        else:
            actual_spent = total - self.stored_value
            self.stored_value = 0.0
            self.total_spent += actual_spent
        self.coupons += qty 
        self.trades.append(f"买入 {qty} 杯 {drink_name}")

    def sell(self, drink_name, qty, price_per_unit):
        # if self.holdings.get(drink_name, 0) >= qty:
        #     self.holdings[drink_name] -= qty
        #     total = price_per_unit * qty
        #     self.trades.append(("sell", drink_name, qty, total))

        if self.holdings.get(drink_name, 0) >= qty:
            self.holdings[drink_name] = self.holdings.get(drink_name, 0) - qty
            total = price_per_unit * qty
            self.stored_value += total
            self.coupons -= qty
            self.trades.append(f"卖出 {qty} 杯 {drink_name}")
             

    def consume(self, drink_name):
        if self.holdings.get(drink_name, 0) > 0:
            self.holdings[drink_name] -= 1
            self.coupons -= 1
            self.coupons_redeemed += 1
            # self.trades.append(("consume", drink_name, 1))
            self.trades.append(f"喝掉 1 杯 {drink_name}")


class ExchangeState:
    def __init__(self, fee=0.5):
        self.current_time = 0 #datetime(2025, 1, 1, 0, 0, 0)#datetime.now()
        self.drinks = {}
        self.users = []
        # self.users = [User(name) for name in ["Alice", "Bob", "Carol", "Dave"]]
        # self.drinks = {
        #     name: Drink(name, init_price)
        #     for name, init_price in {
        #         "啤酒": 10.0,
        #         "红酒": 12.0,
        #         # "威士忌": 15.0,
        #         # "伏特加": 8.0,
        #     }.items()
        # }
        self.history = []
        self.total_recharge = 0.0  # 总营收
        self.total_coupon_count = 0 # 在外总酒券
        self.total_coupon_value = 0.0 #在外总酒券价值
        self.total_stored_value = 0 # 在外总储值金额
        self.net_revenue = 0.0  # 净利润
        self.fee = fee  # 每杯的固定手续费
        # 交易记录，格式：{酒名: [{"time": datetime, "type": "buy"/"sell", "qty": int}, ...]}
        self.trade_records = {}

        # 价格历史，{酒名: [price1, price2, ...]}
        self.price_history = {}

    def get_net_revenue(self):
        # 总营收 - 所有用户酒券总价值 - 所有用户储值余额
        return self.total_recharge - self.get_total_coupon_value() - self.get_total_stored_value()

    def get_total_stored_value(self):
        return sum(user.stored_value for user in self.users)

    def get_total_coupon_value(self):
        prices = self.get_all_drink_prices()
        return sum(user.get_coupon_value(prices) for user in self.users)

    def get_total_coupon_count(self):
        return sum(user.get_coupon_count() for user in self.users)
    
    def get_user_names(self):
        return [u.name for u in self.users]

    def get_drink_names(self):
        return list(self.drinks.keys())

    def get_all_drink_prices(self):
        return {name: drink.price for name, drink in self.drinks.items()}

    def get_user(self, name):
        return next(u for u in self.users if u.name == name)

    def get_price(self, drink_name):
        return self.drinks[drink_name].price

    def record_trade(self, drink_name, price, net_qty):
        # print('record_trade')
        self.trade_records.setdefault(drink_name, []).append({
            "time": self.current_time,
            "price": price,
            "net_qty": net_qty
        })

    def get_trade_df(self, drink_name):
        
        records = self.trade_records.get(drink_name, [])
        # print(records)
        if not records:
            return F.DataFrame(schema=["time", "price", "net_qty"])
        return F.DataFrame(records)
        
    def get_price_history(self, drink_name):
        return self.drinks[drink_name].price_history
    
    def get_time_history(self, drink_name):
        return [record["time"] for record in self.trade_records.get(drink_name, [])]
    
    def get_net_trade_history(self, drink_name):
        net = []
        for record in self.trade_records.get(drink_name, []):
            if record["type"] == "buy":
                net.append(record["qty"])
            else:
                net.append(-record["qty"])
        return net

    def add_trade_record(self, drink_name, trade_type, qty):
        if drink_name not in self.trade_records:
            self.trade_records[drink_name] = []
        self.trade_records[drink_name].append({
            "time": self.current_time,
            "type": trade_type,
            "qty": qty,
        })

    def advance_time(self, minutes):
        self._save_state()
        self.current_time += minutes#timedelta(minutes=minutes)
        for drink_name, drink in self.drinks.items():
            drink.mean_revert(minutes)
            self.record_trade(drink_name, drink.price, 0)

    def rewind_time(self, minutes):
        self._save_state()
        self.current_time -= minutes#timedelta(minutes=minutes)

    def buy(self, user_name, drink_name, qty):
        self._save_state()
        user = self.get_user(user_name)
        drink = self.drinks[drink_name]
        unit_price = drink.price + self.fee
        total_price = unit_price * qty

        # 扣除储值金额，剩余部分加入 total_spent
        if user.stored_value >= total_price:
            # user.stored_value -= total_price
            actual_spent = 0.0
        else:
            actual_spent = total_price - user.stored_value
            # user.stored_value = 0.0
            # user.total_spent -= actual_spent
        self.total_recharge += actual_spent
        
        user.buy(drink_name, qty, unit_price)
        # self.revenue += total_price
        # self.net_revenue += self.fee * qty
        drink.update_price(drink.price_impulse * qty)
        self.record_trade(drink_name, drink.price, qty)

    def sell(self, user_name, drink_name, qty):
        self._save_state()
        user = self.get_user(user_name)
        drink = self.drinks[drink_name]
        user.sell(drink_name, qty, drink.price - self.fee)
        # total = (drink.price - self.fee) * qty
        # self.revenue -= total
        # self.net_revenue -= self.fee * qty
        drink.update_price(-drink.price_impulse * qty)
        self.record_trade(drink_name, drink.price, -qty)

    def consume(self, user_name, drink_name):
        self._save_state()
        user = self.get_user(user_name)
        if user.holdings.get(drink_name, 0) > 0:
            user.consume(drink_name)
            self.net_revenue += self.drinks[drink_name].price

    def undo_last(self):
        if self.history:
            state = self.history.pop()
            self.__dict__ = copy.deepcopy(state.__dict__)

    def _save_state(self):
        self.history.append(copy.deepcopy(self))
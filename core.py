from datetime import datetime, timedelta
import copy

class Drink:
    def __init__(self, name, init_price):
        self.name = name
        self.price = init_price
        self.price_history = [init_price]

    def update_price(self, delta):
        self.price = max(0.01, self.price + delta)
        self.price_history.append(self.price)

    def mean_revert(self, anchor=10.0, strength=0.01):
        self.update_price(strength * (anchor - self.price))


class User:
    def __init__(self, name):
        self.name = name
        self.holdings = {}  # {drink_name: qty}
        self.trades = []

    def buy(self, drink_name, qty):
        self.holdings[drink_name] = self.holdings.get(drink_name, 0) + qty
        self.trades.append(f"买入 {qty} 杯 {drink_name}")

    def sell(self, drink_name, qty):
        self.holdings[drink_name] = self.holdings.get(drink_name, 0) - qty
        self.trades.append(f"卖出 {qty} 杯 {drink_name}")

    def consume(self, drink_name):
        if self.holdings.get(drink_name, 0) > 0:
            self.holdings[drink_name] -= 1
            self.trades.append(f"喝掉 1 杯 {drink_name}")


class ExchangeState:
    def __init__(self):
        self.current_time = datetime.now()
        self.users = [User(name) for name in ["Alice", "Bob", "Carol", "Dave"]]
        self.drinks = {
            name: Drink(name, init_price)
            for name, init_price in {
                "啤酒": 10.0,
                # "红酒": 12.0,
                # "威士忌": 15.0,
                # "伏特加": 8.0,
            }.items()
        }
        self.history = []
        self.revenue = 0.0
        self.fee = 0.5  # 每杯的固定手续费

    def get_user_names(self):
        return [u.name for u in self.users]

    def get_drink_names(self):
        return list(self.drinks.keys())

    def get_user(self, name):
        return next(u for u in self.users if u.name == name)

    def get_price(self, drink_name):
        return self.drinks[drink_name].price

    def get_price_history(self, drink_name):
        return self.drinks[drink_name].price_history

    def advance_time(self, minutes):
        self._save_state()
        self.current_time += timedelta(minutes=minutes)
        for drink in self.drinks.values():
            drink.mean_revert()

    def rewind_time(self, minutes):
        self._save_state()
        self.current_time -= timedelta(minutes=minutes)

    def buy(self, user_name, drink_name, qty):
        self._save_state()
        user = self.get_user(user_name)
        drink = self.drinks[drink_name]
        user.buy(drink_name, qty)
        total = (drink.price + self.fee) * qty
        self.revenue += total
        drink.update_price(+0.2 * qty)

    def sell(self, user_name, drink_name, qty):
        self._save_state()
        user = self.get_user(user_name)
        drink = self.drinks[drink_name]
        user.sell(drink_name, qty)
        total = (drink.price - self.fee) * qty
        self.revenue -= total
        drink.update_price(-0.2 * qty)

    def consume(self, user_name, drink_name):
        self._save_state()
        user = self.get_user(user_name)
        user.consume(drink_name)

    def undo_last(self):
        if self.history:
            state = self.history.pop()
            self.__dict__ = copy.deepcopy(state.__dict__)

    def _save_state(self):
        self.history.append(copy.deepcopy(self))
import time


def waiter():
    cook("Pasta", 2)
    cook("Caesar Salad", 3)
    cook("Lamb Chops", 6)


def cook(order, time_to_prepare):
    print(f"Getting {order} order")
    time.sleep(time_to_prepare)
    print(order, "ready")


if __name__ == "__main__":
    waiter()

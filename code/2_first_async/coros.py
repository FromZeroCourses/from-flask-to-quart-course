import asyncio
import time


async def waiter() -> None:
    await cook("Pasta", 2)
    await cook("Caesar Salad", 3)
    await cook("Lamb Chops", 6)


def cook(order, time_to_prepare):
    print(f"Getting {order} order")
    time.sleep(time_to_prepare)
    print(order, "ready")


asyncio.run(waiter())

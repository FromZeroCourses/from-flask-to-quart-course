import asyncio
import time


async def waiter() -> None:
    await cook("Pasta", 8)
    await cook("Caesar Salad", 3)
    await cook("Lamb Chops", 16)


def cook(order, time_to_prepare):
    print(f"Getting {order} order")
    time.sleep(time_to_prepare)
    print(order, "ready")


asyncio.run(waiter())

import asyncio
import time


async def waiter() -> None:
    await cook("Pasta", 8)
    await cook("Caesar Salad", 3)
    await cook("Lamb Chops", 16)


async def cook(order: str, time_to_prepare: int) -> None:
    print(f"Getting {order} order")
    await asyncio.sleep(time_to_prepare)
    print(order, "ready")


asyncio.run(waiter())

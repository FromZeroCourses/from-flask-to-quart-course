from quart import Blueprint, current_app
from sqlalchemy import select, insert, update

from counter.models import counter_table

counter_app = Blueprint("counter_app", __name__)


@counter_app.route("/")
async def init() -> str:
    engine = current_app.dbc  # type: ignore
    async with engine.begin() as conn:
        rows = (await conn.execute(select(counter_table))).fetchall()
        if not rows:
            await conn.execute(insert(counter_table).values(count=1))
            count = 1
        else:
            row = rows[0]
            count = row.count + 1
            await conn.execute(
                update(counter_table)
                .where(counter_table.c.id == row.id)
                .values(count=count)
            )
    return "<h1>Counter: " + str(count) + "</h1>"

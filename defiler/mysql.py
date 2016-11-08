from aiomysql import create_pool


class DB:

    async def connect(self, **kwargs):
        self.pool = await create_pool(**kwargs)

    async def check_auth(self, username, password):
        async with self.pool.get() as conn:
            cur = await conn.cursor()
            await cur.execute(("SELECT gas FROM users WHERE "
                               "username=%s AND password=PASSWORD(%s)"),
                              (username, password))
            value = await cur.fetchone()
            return value

    async def execute(self, query, *args):
        async with self.pool.get() as conn:
            cur = await conn.cursor()
            await cur.execute(query, *args)
            data = await cur.fetchall()
            return data

    async def get_streams(self, provider=None):
        async with self.pool.get() as conn:
            cur = await conn.cursor()
            await cur.execute("SELECT provider, slug, name FROM streams")
            streams = await cur.fetchall()
            return streams

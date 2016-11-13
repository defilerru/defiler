from aiomysql import create_pool
import pymysql.err

GET_USER_BY_TWITCH = ("SELECT u.id, u.nickname "
                      "FROM twitch AS t LEFT OUTER JOIN users AS u "
                      "ON t.user_id=u.id WHERE t.username=%s")
CREATE_TWITCH_USER = ("INSERT INTO twitch(username) VALUES(%s)")
CREATE_SESSION_QUERY = ("INSERT INTO sessions(id, user_id, nickname, created) "
                        "VALUES(%s, %s, %s, NOW())")
DELETE_SESSION_QUERY = ("DELETE FROM sessions WHERE id=%s")
GET_STREAMS_QUERY = "SELECT slug, name FROM streams WHERE provider=%s"

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

    async def delete_session(self, sid):
        async with self.pool.get() as conn:
            cur = await conn.cursor()
            await cur.execute(DELETE_SESSION_QUERY, (sid))
            await conn.commit()

    async def create_session(self, sid, uid, nickname):
        async with self.pool.get() as conn:
            cur = await conn.cursor()
            await cur.execute(CREATE_SESSION_QUERY, (sid, uid, nickname))
            await conn.commit()

    async def get_or_create_user_by_twitch(self, twitch_username):
        """
        :returns tuple: (user_id, nickname)
        """
        async with self.pool.get() as conn:
            cur = await conn.cursor()
            try:
                ret = await cur.execute(CREATE_TWITCH_USER, (twitch_username, ))
                await conn.commit()
                return (None, twitch_username)
            except pymysql.err.IntegrityError:
                pass
            await cur.execute(GET_USER_BY_TWITCH, (twitch_username, ))
            data = await cur.fetchall()
            if data[0][0]:
                return data
            return (None, twitch_username)

    async def execute(self, query, *args):
        async with self.pool.get() as conn:
            cur = await conn.cursor()
            await cur.execute(query, *args)
            data = await cur.fetchall()
            return data

    async def get_streams(self, provider):
        return await self.execute(GET_STREAMS_QUERY, (provider, ))


channel = "#" + provider + "/" + slug
e.g. #twitch_dyoda

METHODS
#######

["login", {username: string, password: string}]
["logout", {}]
["chat", {channel: string, message: string}]
["join", {channel: string}]
["leave", {channel: string}]

EVENTS
######

["AUTH", {success: bool, nickname: string, uid: int}]
["LOGOUT", {}]
["CHAT", {channel: string, nickname: string, message: string}]
["STREAM", {provider: string, slug: string, data: {}}]
["STREAM_OFFLINE", {provider: string, slug: string}]
["USER_ONLINE", {nickname: string}]
["USER_OFFLINE", {nickname: string}]

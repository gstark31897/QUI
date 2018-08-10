from matrix_client.client import MatrixClient
import time

client = MatrixClient("http://167.99.238.80:8008")

# New user
#token = client.register_with_password(username="foobar", password="monkey")

def listener(event):
    print(event)

# Existing user
token = client.login_with_password(username="foobar", password="monkey")
client.add_listener(listener)

#room = client.create_room("my_room_alias")
room = client.join_room("#my_room_alias:teamspeak.sigmapenguinplace.net")
room.send_text("Hello!")

while True:
    client.listen_for_events()

import socket

from pl1compinpy.runtime import SocketFileDescriptor, SocketStreamRuntime


runtime = SocketStreamRuntime()
left, right = socket.socketpair()
try:
    runtime.adopt("CLIENT", left)
    runtime.adopt("SERVER", right)

    client = SocketFileDescriptor("CLIENT", recfm="V", text=True)
    server = SocketFileDescriptor("SERVER", recfm="V", text=True)

    runtime.write_record(client, "HELLO AS A RECORD")
    print(runtime.read_record(server))
finally:
    runtime.close_all()

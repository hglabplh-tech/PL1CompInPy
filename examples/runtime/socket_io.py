from pl1compinpy.runtime import SocketDescriptor, SocketRuntime


runtime = SocketRuntime()
try:
    server = runtime.listen(SocketDescriptor.tcp_server("SERVER"))
    client = runtime.connect(SocketDescriptor.tcp_client("CLIENT", server.address[0], server.address[1]))
    accepted = runtime.accept("SERVER", "ACCEPTED")

    runtime.send("CLIENT", "HELLO")
    print(runtime.receive("ACCEPTED", 5).decode("utf-8"))
finally:
    runtime.close_all()

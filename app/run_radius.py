try:
    from app.radius import FakeServer
    FakeServer.RunServer()
except Exception as e:
    print("Oops!", e.__class__, "occurred.") 
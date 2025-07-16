from dashboard import create_app, socketio, app

if __name__ == '__main__':
    create_app()
    socketio.run(app)

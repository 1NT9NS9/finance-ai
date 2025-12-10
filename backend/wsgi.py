import os

from backend.api.app import create_app


app = create_app()


if __name__ == "__main__":
    # Lightweight production server for Windows/Linux
    from waitress import serve

    port = int(os.getenv("PORT", "5000"))
    serve(app, host="0.0.0.0", port=port)



from studypdf.app_factory import create_app
from studypdf.db import get_db


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

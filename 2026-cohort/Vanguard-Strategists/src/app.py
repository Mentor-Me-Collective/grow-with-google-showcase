import os
from dotenv import load_dotenv
from lib import create_app

load_dotenv()
app = create_app()

if __name__ == '__main__':
    app.run(host=os.getenv("HOST"), port=int(os.getenv("PORT")), debug=os.getenv("FLASK_DEBUG").lower() == "true")

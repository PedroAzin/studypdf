import logging
import os

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()

from studypdf.app_factory import create_app

print(f"[config] STUDYPDF_UNDERSTANDING_CHECKS={os.environ.get('STUDYPDF_UNDERSTANDING_CHECKS', '(nao definida)')!r}")

try:
    app = create_app()
except Exception:
    logging.getLogger(__name__).exception("Falha ao iniciar StudyPDF")
    raise


if __name__ == "__main__":
    app.run()

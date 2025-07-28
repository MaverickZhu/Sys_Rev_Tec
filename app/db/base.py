# Import all the models, so that Base has them before being
# imported by Alembic

from app.db.base_class import Base  # noqa
from app.models.document import Document  # noqa
from app.models.ocr_result import OCRResult  # noqa
from app.models.project import Project  # noqa
from app.models.user import User  # noqa

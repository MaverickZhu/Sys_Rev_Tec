# Import all the models, so that Base has them before being
# imported by Alembic

from app.db.base_class import Base  # noqa
from app.models.document import Document  # noqa
from app.models.ocr import OCRResult  # noqa
from app.models.oauth2_client import OAuth2Client, OAuth2AuthorizationCode  # noqa
from app.models.project import Project  # noqa
from app.models.token_blacklist import TokenBlacklist  # noqa
from app.models.user import User  # noqa

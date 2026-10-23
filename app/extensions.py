from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

bcrypt = Bcrypt()
csrf = CSRFProtect()
db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address, default_limits=["300 per hour"])
login_manager = LoginManager()
migrate = Migrate()

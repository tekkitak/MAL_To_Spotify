from flask_security.core        import Security
from flask_security.datastore   import SQLAlchemyUserDatastore
from flask_session              import Session  # type: ignore -- package stub issue...

from model.database import db, User, Role


def register_extensions(app) -> None:
    """
    Registers all extensions externally 
    so they can be imported without circular imports
    """
    db.init_app(app)
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    app.security = Security(app, user_datastore)
    Session(app)

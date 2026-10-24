import pytest
from app import create_app
from models import db, User, Loan, EMISchedule, Payment

@pytest.fixture
def app():
    """Create and configure a clean testing application instance with an isolated database."""
    test_app = create_app(config_name="testing")

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click/CLI commands."""
    return app.test_cli_runner()


@pytest.fixture
def registered_user(app):
    """Creates a sample registered user."""
    with app.app_context():
        user = User(
            full_name="Rajesh Sharma",
            email="rajesh@example.com"
        )
        user.set_password("SecurePass123!")
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.user_id)


@pytest.fixture
def second_user(app):
    """Creates a second user for testing cross-user access isolation."""
    with app.app_context():
        user = User(
            full_name="Priya Patel",
            email="priya@example.com"
        )
        user.set_password("PriyaSecret456!")
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.user_id)


@pytest.fixture
def authenticated_client(client, registered_user):
    """A test client with an authenticated session for registered_user."""
    with client.session_transaction() as sess:
        sess["user_id"] = registered_user.user_id
        sess["user_name"] = registered_user.full_name
        sess["user_email"] = registered_user.email
    return client

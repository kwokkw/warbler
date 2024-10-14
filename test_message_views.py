"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

# os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
os.environ['DATABASE_URL'] = "postgresql://postgres:17273185@localhost/warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False
# Make Flask errors be real errors, not HTML pages with error info
app.config['TESTING'] = True
# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            # this statement accesses the Flask sesseion, 
            # allowing us to modify it.
            # Flask sessions are usually stored client-side 
            # (using cookies), but here during the test, 
            # the `session_transaction()` allows us to directly
            # interact with and modify the session server-side 
            # for testing purposes.
            with c.session_transaction() as sess:
                # this simulates logging in by manually setting 
                # the session value to represent the logged-in
                # user's ID.
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

# 1. When you’re logged in, can you see the follower / following pages for any user?
# 2. When you’re logged out, are you disallowed from visiting a user’s follower / following pages?
# 3. When you’re logged in, can you add a message as yourself?
# 4. When you’re logged in, can you delete a message as yourself?
# 5. When you’re logged out, are you prohibited from adding messages?
# 6. When you’re logged out, are you prohibited from deleting messages?
# 7. When you’re logged in, are you prohibiting from adding a message as another user?
# 8. When you’re logged in, are you prohibiting from deleting a message as another user?
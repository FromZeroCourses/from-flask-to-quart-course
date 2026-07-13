# QuartFeed, an SSE Application using PostgreSQL <!-- 5 -->

## Introduction to Server Sent Events <!-- 5.1 -->
Server Sent Events, or SSEs, or EventSource in JavaScript, are an extension to HTTP that allow a client to keep a connection open to a server, thereby allowing the server to send events to the client as it chooses.

By default, the server sends updates with a `data` payload. You can also have an `event` type, which by default is `message`, but could be things like `add` or `remove`. Additionally it has an `id` parameter that allows the client to continue where it left off if the connection was lost.

We are going to build a lightweight version of the popular FriendFeed website, one of the pioneers in the social media space. using Quart and SSE.

For our FriendFeed clone we’ll have the event type to be either `post`, which is a new post, `like` if some one liked the post and `comment` if it’s a comment to a `post`.

For a more complex version or exercise to students, we could also have `groups`, which could be distinct `/sse` endpoints and `like` events for comments.

## From Boilerplate to QuartFeed <!-- 5.2 -->

Now that we understand what Server Sent Events are, let's start building QuartFeed. Before we get to the live feed, though, we need the pieces underneath it: users who can register and log in, follow each other, and write posts. So the plan for this chapter is to build those layers one at a time, and only wire up the real-time feed once the data is there to push.

The great news is that we don't start from a blank folder. In the previous chapter we built a Quart Postgres counter, and I told you it would double as a boilerplate for any database-driven Quart project. This is where that pays off: QuartFeed begins as a copy of that counter app.

So make a copy of your counter application folder and rename the copy to `quartfeed_app`. Everything we need is already there: the `Dockerfile`, the `docker-compose.yml`, the async `db.py`, the application factory, and the Alembic migration setup.

If any cache folders came along for the ride, like a `__pycache__` or a stray `migrations/versions` file, go ahead and delete them so we start clean.

The first thing we'll do is rename the project. Open `pyproject.toml` and change the project name to `quartfeed-app`:

{lang=toml,line-numbers=on,starting-line-number=1}
```
[project]
name = "quartfeed-app"
version = "0.1.0"
```

[Save the file](https://fmze.co/fftq-5.2.1).

Our counter had a single blueprint called `counter`. QuartFeed's first module is the user, so let's rename the `counter` folder to `user`. This is where registration, login, and profiles will live.

Now open the `models.py` file inside that new `user` folder. The counter table doesn't make sense anymore, so we'll replace it with our first real model, the `user` table:

{lang=python,line-numbers=on}
```
from sqlalchemy import Column, Integer, String, Table

from db import metadata

user_table = Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(15), index=True, unique=True),
    Column("password", String(128)),
)
```

Just like our counter model, we import `Table`, `Column`, and our application-wide `metadata` object. This time we also import `String`, since our columns hold text instead of numbers.

We define a table named `user` with the usual auto-incrementing `id` as the primary key. Then comes the `username`, a string capped at fifteen characters.

Notice the two extra properties on `username`: we set `index` to `True` because we'll constantly look users up by their username, and an index makes those lookups fast. We also set `unique` to `True`, because no two people can share a username.

The last column is `password`, a string of length one hundred and twenty eight. That length isn't arbitrary: we're going to store a hashed password, never the real one, and the hashing algorithm we'll use always produces a hash exactly that long.

[Save the file](https://fmze.co/fftq-5.2.2).

Next let's give this module a minimal controller so the app boots. Open `user/views.py` and replace the counter view with a placeholder registration route:

{lang=python,line-numbers=on}
```
from quart import Blueprint

user_app = Blueprint("user_app", __name__)


@user_app.route("/register")
async def register() -> str:
    return "<h1>User Registration</h1>"
```

We create a blueprint called `user_app`, and a single `/register` route that, for now, just returns a bit of HTML. We're only proving the wiring works. We'll build the real form in the next lesson.

[Save the file](https://fmze.co/fftq-5.2.3).

Now we point the application factory at the new blueprint. Open `application.py` and update the import and the registration to use `user_app`:

{lang=python,line-numbers=on,starting-line-number=8}
```
    from user.views import user_app

    app.register_blueprint(user_app)
```

[Save the file](https://fmze.co/fftq-5.2.4).

There's one more rename to do, this time in our container config, since we renamed the project folder. Open the `Dockerfile` and change every `counter_app` reference to `quartfeed_app`:

{lang=yml,line-numbers=on,starting-line-number=4}
```
WORKDIR /quartfeed_app
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

COPY pyproject.toml uv.lock /quartfeed_app/
```

[Save the file](https://fmze.co/fftq-5.2.5) and do the same in `docker-compose.yml`, where the volume mounts our code into the container:

{lang=yml,line-numbers=on,starting-line-number=7}
```
    volumes:
      - ./:/quartfeed_app
```

[Save the file](https://fmze.co/fftq-5.2.6).

Now let's deal with migrations. Because this is a brand new application with a brand new database, open `migrations/env.py` and update the model import so Alembic tracks the `user` table instead of the old `counter` table:

{lang=python,line-numbers=on,starting-line-number=16}
```
from user.models import user_table  # noqa: F401
```

Remember the rule from the counter app: every time we add a new model, we import it here so Alembic can see it when it generates migrations. We'll be back in this file a few times this chapter.

[Save the file](https://fmze.co/fftq-5.2.7).

We're ready to create the database. First, bring up just the Postgres container so we have something to migrate against:

{lang=bash,line-numbers=off}
```
$ docker compose up -d db
```

Then build the web image so our renamed project and its packages are installed inside it:

{lang=bash,line-numbers=off}
```
$ docker compose build web
```

Now we generate our first migration. Just like the counter app, we run Alembic inside the web container:

{lang=bash,line-numbers=off}
```
$ docker compose run --rm web uv run alembic revision --autogenerate -m "create user table"
INFO  [alembic.autogenerate.compare] Detected added table 'user'
INFO  [alembic.autogenerate.compare] Detected added index 'ix_user_username' on '['username']'
```

Alembic compared our metadata against the empty database and generated a migration that creates the `user` table and the index on `username`. Take a quick look at the new file in `migrations/versions` to confirm it looks right, then apply it:

{lang=bash,line-numbers=off}
```
$ docker compose run --rm web uv run alembic upgrade head
```

Our database now has a `user` table, ready to hold accounts. In the next lesson we'll let people actually create one.

## Registering Users with quart-wtforms <!-- 5.3 -->

We have a `user` table, so now we need a registration form that writes into it. Building forms by hand — reading each field off the request, validating it, and guarding against cross site request forgery — is tedious and easy to get wrong, so we want a library to handle it for us.

In the Flask world, that library is Flask-WTF: it takes care of form fields, validation, and CSRF protection. But there's a catch, and it's the important lesson of this section. Flask-WTF is built around Flask's **synchronous** request object, so it simply does not work inside an async Quart app. And that's the takeaway to hold onto: in an async application, you can't reach for a synchronous library and expect it to work. If a package wasn't written for async — if there's no Quart-flavored version of it — that's usually a sign you shouldn't be using it in a Quart app at all.

![Flask-WTF is built on Flask's synchronous request object, so it can't work inside Quart's async event loop.](images/5.3-scene2-img1.png)

Happily, there is a Quart-flavored version here. It's called `quart-wtforms`, and it brings WTForms to Quart the async way, giving us validation and CSRF protection for free. So we'll use it and let it do the heavy lifting.

![quart-wtforms brings WTForms to Quart the async way, giving us form validation and CSRF protection for free.](images/5.3-scene2-img2.png)

Let's add it. Just like every package, we declare it with `uv add --no-sync` so it gets installed when Docker rebuilds the image:

{lang=bash,line-numbers=off}
```
$ uv add --no-sync quart-wtforms
```

We're storing passwords, so we also need a way to hash them. We'll use `passlib`, a well tested password hashing library. Add it the same way:

{lang=bash,line-numbers=off}
```
$ uv add --no-sync passlib
```

Since we added packages, rebuild the web image so they land inside the container:

{lang=bash,line-numbers=off}
```
$ docker compose build web
```

WTForms and its CSRF protection need a secret key to sign tokens, and we already have a `SECRET_KEY` from the counter boilerplate. We just need to switch CSRF on. Open `.quartenv` and add a flag for it:

{lang=python,line-numbers=on,starting-line-number=8}
```
WTF_CSRF_ENABLED=1
```

[Save the file](https://fmze.co/fftq-5.3.1) and read it into your settings. Open `settings.py` and add:

{lang=python,line-numbers=on,starting-line-number=9}
```
WTF_CSRF_ENABLED = os.environ.get("WTF_CSRF_ENABLED", "1") == "1"
```

We read it as a string and compare it to `"1"`, so the value ends up as a real boolean. We default it to on, and later, in our tests, we'll flip it off so we don't have to deal with tokens there.

[Save the file](https://fmze.co/fftq-5.3.2).

Now the form itself. Create a `forms.py` file inside the `user` folder:

{lang=python,line-numbers=on}
```
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length

from quart_wtf import QuartForm


class UserForm(QuartForm):
    """Used for both registration and login."""

    username = StringField(
        "Username",
        validators=[DataRequired(), Length(max=15)],
        render_kw={"autocomplete": "off"},
    )
    password = PasswordField("Password", validators=[DataRequired()])
```

We import two field types, a `StringField` for the username and a `PasswordField` for the password, plus two validators. Then we import `QuartForm`, the async base class our form inherits from.

Our `UserForm` defines just two fields. The `username` is required and limited to fifteen characters, matching our database column, and we ask the browser not to autocomplete it. The `password` is also required.

Notice how declarative this is. We describe the fields and their rules once, and the library handles rendering, reading the values, and validating them. That same `UserForm` will drive both registration here and login in the next lesson.

[Save the file](https://fmze.co/fftq-5.3.3).

Before we write the view, we need templates to render. We'll start with a base layout that every page extends. Create a `templates` folder at the project root and add `base.html`. It's a longer file, so we'll build it in two parts, starting with the document head:

{lang=html,line-numbers=on}
```
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- Bootstrap CSS (CDN) -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"
        integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">

    <title>{% block title %}{% endblock %} - QuartFeed</title>
</head>
```

This is a standard HTML shell. In the head we pull in Bootstrap's CSS from their CDN so our pages look decent without us writing much styling, and we define a `title` block each page can fill in. Now the body:

{lang=html,line-numbers=on,starting-line-number=15}
```
<body>
    <div class="container py-3">
        {% block content %}{% endblock %}
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p"
        crossorigin="anonymous"></script>
    {% block scripts %}{% endblock %}
</body>

</html>
```

In the body we have a container with a `content` block, which is where each page's real content will go. At the bottom we load Bootstrap's JavaScript, and leave a scripts block for pages that need their own JavaScript later, like our live feed.

[Save the file](https://fmze.co/fftq-5.3.4).

Every page needs a navigation bar, so let's create `navbar.html` in the same `templates` folder. For now it just links to Login and Register:

{lang=html,line-numbers=on}
```
<nav class="navbar navbar-expand-lg navbar-light bg-light mb-3">
    <div class="container-fluid">
        <a class="navbar-brand" href="#">QuartFeed</a>
        <div class="navbar-nav ms-auto">
            <a class="nav-link" href="{{ url_for('user_app.login') }}">Login</a>
            <a class="nav-link" href="{{ url_for('user_app.register') }}">Register</a>
        </div>
    </div>
</nav>
```

This is Bootstrap's navbar component with our brand name and two links. Notice we build the link targets with `url_for` rather than hardcoding paths. That's a best practice: if a route ever changes, the links follow automatically.

[Save the file](https://fmze.co/fftq-5.3.5).

WTForms can render fields for us, but we want each one wrapped in Bootstrap markup with its validation errors shown. Rather than repeat that markup for every field, we'll write a small Jinja macro. Create `_formhelpers.html` in the `templates` folder:

{lang=html,line-numbers=on}
```
{% macro render_field(field) %}
<div class="mb-3">
    {{ field.label(class="form-label") }}
    {{ field(class="form-control")|safe }}
    {% if field.errors %}
    <ul class="text-danger">
        {% for error in field.errors %}
        <li>{{ error }}</li>
        {% endfor %}
    </ul>
    {% endif %}
</div>
{% endmacro %}
```

A Jinja macro is like a reusable function for templates. This one takes a form field and renders its label, the input itself, and, if the field failed validation, a red list of the error messages. We'll call `render_field` for every field so our forms stay consistent and short.

![One render_field macro expands every form field into its label, input, and validation errors — write once, reuse.](images/5.3-scene9-img1.png)

[Save the file](https://fmze.co/fftq-5.3.6).

Now the registration page. Create a user folder inside `templates` and add `register.html`:

{lang=html,line-numbers=on}
```
{% extends "base.html" %}

{% block title %}Registration{% endblock %}

{% block content %}

{% include "navbar.html" %}

<div class="row">
    <div class="col-md-6 offset-md-3">

        <h3>Registration</h3>

        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}

        {% from "_formhelpers.html" import render_field %}

        <form method="POST" action="{{ url_for('.register') }}" role="form">
            {{ render_field(form.username) }}
            {{ render_field(form.password) }}
            {{ form.csrf_token }}
            <button type="submit" class="btn btn-primary">Register</button>
        </form>

    </div>
</div>

{% endblock %}
```

We extend `base.html`, set the title, and drop the navbar at the top of the content block. Then we center a column on the page and show an error alert if the view passed one in.

We import our `render_field` macro and use it for the username and password, so both come out as nicely styled Bootstrap fields. Then we submit the form with a button.

![The login template reuses the render_field macro for the username and password fields.](images/5.3-scene10-img1.png)

The one line worth pausing on is `{{ form.csrf_token }}`. That renders a hidden field holding the CSRF token, and this single line is our entire cross site request forgery protection. The library generated the token, put it in the form, and will verify it when the form comes back. Done by hand, CSRF protection is fiddly and easy to get subtly wrong — here it's one line.

[Save the file](https://fmze.co/fftq-5.3.7).

Now we can write the real registration view. Open `user/views.py` and rebuild it:

{lang=python,line-numbers=on}
```
from typing import Optional, Union

from passlib.hash import pbkdf2_sha256
from quart import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from sqlalchemy import insert, select

from user.forms import UserForm
from user.models import user_table

user_app = Blueprint("user_app", __name__)
```

We import quite a few things. From `passlib` we bring in `pbkdf2_sha256`, the hashing scheme we'll use. From `quart` we import the usual helpers plus `flash`, which lets us stash a one time message for the next page. And we pull in `insert` and `select` from SQLAlchemy, our form, and our model.

Now the register function itself:

{lang=python,line-numbers=on,starting-line-number=20}
```
@user_app.route("/register", methods=["GET", "POST"])
async def register() -> Union[str, Response]:
    form = await UserForm.create_form()
    error: Optional[str] = None

    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            existing = (
                await conn.execute(
                    select(user_table).where(
                        user_table.c.username == form.username.data
                    )
                )
            ).fetchone()

            if existing is not None:
                error = "User already exists"
            else:
                password_hash = pbkdf2_sha256.hash(form.password.data)
                await conn.execute(
                    insert(user_table).values(
                        username=form.username.data, password=password_hash
                    )
                )

        if not error:
            await flash("User registered successfully, please login")
            return redirect(url_for(".login"))

    return await render_template("user/register.html", form=form, error=error)
```

Our route accepts both `GET` and `POST`. We start by creating the form with `await UserForm.create_form()`. Because reading the incoming request is asynchronous in Quart, building the form is an awaitable, so we `await` it.

The heart of it is `await form.validate_on_submit()`. On a `GET` this is false, so we skip straight to rendering the empty form. On a `POST` it checks the CSRF token and runs our validators, and only returns true if everything passed. That one call replaces all the manual request-method checks and field validation we'd otherwise have to write ourselves.

Inside, we grab our database engine from `current_app.dbc`, exactly as we did in the counter app, and open a transaction. First we select any user with the same username. If we find one, we set an error, because usernames must be unique.

If the name is free, we hash the password with `pbkdf2_sha256.hash`. This turns the plain password into a long, scrambled string that we store instead of the real thing. Even we can't reverse it, which is the whole point: if our database ever leaks, the passwords are useless.

Then we insert the new user with the hashed password. If there were no errors, we flash a success message and redirect to the login page, which we'll build next. Otherwise we fall through and re-render the form with the error shown.

[Save the file](https://fmze.co/fftq-5.3.8).

Before we try this out, there's one loose end. Our register view redirects to `login` when a signup succeeds, and our navbar links to it too, but we haven't built that route yet, so the page would crash if we loaded it now. So, exactly like we did with `register` earlier, let's add a placeholder `login` route just below it for now. We'll build the real login page in the next lesson.

{lang=python,line-numbers=on,starting-line-number=51}
```
@user_app.route("/login")
async def login() -> str:
    return "<h1>Login</h1>"
```

[Save the file](https://fmze.co/fftq-5.3.9).

Let's try it. Bring up the stack and rebuild so the new packages are in place:

{lang=bash,line-numbers=off}
```
$ docker compose up --build
```

Head to `localhost:5000/register`. Submit the form empty and you'll see the required-field errors, courtesy of our validators. Now register a real username and password. The app hashes the password, saves the user, and redirects you to the login page. Try registering that same username again and you'll get our "User already exists" message. And just like that, QuartFeed has its first real users, passwords hashed and accounts saved. But signing up is only half the story—those users still can't get back in. That's next: we'll log them in, give them a session, and let them log out.

## Logging In, Sessions, and Logout <!-- 5.4 -->

We can create users, but they can't come back and prove who they are. In this lesson we'll add login and logout, and along the way meet the session, which is how a web app remembers you from one request to the next.

Logging in is the mirror image of registering. We look up the user by their username, then check that the password they typed matches the hash we stored. Both register and login need that "find a user by username" lookup, so this is a good moment to pull it into a shared helper instead of writing the query twice.

![Register and login both share one username lookup](images/5.4-scene2-img1.png)

Let's create a `utils` folder at the project root, with an empty `__init__.py` so it's a package, and a `helpers.py` file inside it:

{lang=python,line-numbers=on}
```
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.engine import Row

from user.models import user_table


async def get_user_by_username(conn: Any, username: str) -> Optional[Row]:
    result = await conn.execute(
        select(user_table).where(user_table.c.username == username)
    )
    return result.fetchone()
```

This is just the username lookup we wrote inline in the register view, moved into a function. It takes an open connection and a username, runs the select, and returns the row or `None`. We'll keep adding small helpers like this to `utils/helpers.py` as the app grows.

[Save the file](https://fmze.co/fftq-5.4.1).

Let's use it back in `user/views.py`. First update the imports to bring in `session` from Quart and our new helper `get_user_by_username`:

{lang=python,line-numbers=on,starting-line-number=4}
```
from quart import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    session,
    url_for,
)
from sqlalchemy import insert, select

from utils.helpers import get_user_by_username
from user.forms import UserForm
from user.models import user_table
```

Now that we have the helper, simplify the duplicate check in `register` to use it: replace the inline select with a call to `get_user_by_username(conn, form.username.data)`.

{lang=python,line-numbers=on,starting-line-number=28}
```
    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            existing = await get_user_by_username(conn, form.username.data)

            if existing is not None:
                error = "User already exists"
```

[Save the file](https://fmze.co/fftq-5.4.2) and let's write the login view below `register`:

{lang=python,line-numbers=on,starting-line-number=40}
```
@user_app.route("/login", methods=["GET", "POST"])
async def login() -> Union[str, Response]:
    form = await UserForm.create_form()
    error: Optional[str] = None

    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            user = await get_user_by_username(conn, form.username.data)

        if user is None or not pbkdf2_sha256.verify(
            form.password.data, user.password
        ):
            error = "Invalid username or password"
        else:
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("post_app.home"))

    return await render_template("user/login.html", form=form, error=error)
```

The top mirrors registration: same form, same `validate_on_submit`. We look up the user by their username using our helper.

Then comes the check. We reject the login if there's no such user, or if `pbkdf2_sha256.verify` says the typed password doesn't match the stored hash. `verify` hashes the incoming password and compares, so we never have to un-hash anything.

Here's a subtle but important security choice: whether the username was wrong or the password was wrong, we return the exact same message, "Invalid username or password". If we said "no such user" versus "wrong password", we'd be telling an attacker which usernames exist. So we stay vague on purpose.

If the credentials are good, we log the person in by storing their id and username in the `session`. The session is a small, signed cookie Quart manages for us. On every later request we can read `session["user_id"]` to know who's making it. Then we redirect to `post_app.home` — but that endpoint doesn't exist yet, so login has nowhere to land. Let's build a minimal home page for it.

Create a `post` package with a `views.py`. Later this chapter it'll grow into the friend feed; for now it just needs a home route:

{lang=python,line-numbers=on}
```
from quart import Blueprint, redirect, render_template, session, url_for

post_app = Blueprint("post_app", __name__)


@post_app.route("/")
async def home():
    if session.get("username") is None:
        return redirect(url_for("user_app.login"))

    return await render_template("post/home.html")
```

The route is guarded: if there's no `username` in the session, a logged-out visitor is bounced back to login. Otherwise we render the home template.

Register the blueprint in `application.py`, right alongside `user_app`:

{lang=python,line-numbers=on,starting-line-number=13}
```
    from user.views import user_app
    from post.views import post_app

    app.register_blueprint(user_app)
    app.register_blueprint(post_app)
```

Now the template. Create `templates/post/home.html`:

{lang=html,line-numbers=on}
```
{% extends "base.html" %}

{% block title %}Home{% endblock %}

{% block content %}

{% include "navbar.html" %}

<div class="row">
    <div class="col-md-6 offset-md-3">

        {% for message in get_flashed_messages() %}
        <div class="alert alert-success">{{ message }}</div>
        {% endfor %}

        <h1>Welcome, {{ session.username }}!</h1>
        <p>You're logged in. The friend feed lands here in the next section.</p>

    </div>
</div>

{% endblock %}
```

It reads `session.username` straight from the session to greet the user by name — visible proof the login stuck. Now login has a real page to land on.

[Save the file](https://fmze.co/fftq-5.4.3).

Login renders its own template, very similar to register. Create `templates/user/login.html`:

{lang=html,line-numbers=on}
```
{% extends "base.html" %}

{% block title %}Login{% endblock %}

{% block content %}

{% include "navbar.html" %}

<div class="row">
    <div class="col-md-6 offset-md-3">

        {% for message in get_flashed_messages() %}
        <div class="alert alert-success">{{ message }}</div>
        {% endfor %}

        <h3>Login</h3>

        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}

        {% from "_formhelpers.html" import render_field %}

        <form method="POST" action="{{ url_for('.login') }}" role="form">
            {{ render_field(form.username) }}
            {{ render_field(form.password) }}
            {{ form.csrf_token }}
            <button type="submit" class="btn btn-primary">Login</button>
        </form>

    </div>
</div>

{% endblock %}
```

It's the register template with the labels changed. The one new piece is the loop over `get_flashed_messages`. That's where the "please login" message we flashed after registration shows up, in a green success alert. Flash messages appear exactly once, on the very next page, and then they're gone.

[Save the file](https://fmze.co/fftq-5.4.4).

Now logout, which is the simplest view we'll write. Add it below `login`:

{lang=python,line-numbers=on,starting-line-number=60}
```
@user_app.route("/logout")
async def logout() -> Response:
    session.pop("user_id", None)
    session.pop("username", None)
    await flash("You have been logged out")
    return redirect(url_for(".login"))
```

Logging out just means forgetting who the user is, so we pop their id and username out of the session. We flash a goodbye message and send them back to the login page. No password, no database, just clearing the cookie.

[Save the file](https://fmze.co/fftq-5.4.5).

The last thing is to make the navbar aware of whether someone is logged in. Open `navbar.html` and make the right side depend on the session:

{lang=html,line-numbers=on,starting-line-number=4}
```
        <div class="navbar-nav ms-auto">
            {% if session.username %}
            <a class="nav-link" href="{{ url_for('user_app.logout') }}">Logout</a>
            {% else %}
            <a class="nav-link" href="{{ url_for('user_app.login') }}">Login</a>
            <a class="nav-link" href="{{ url_for('user_app.register') }}">Register</a>
            {% endif %}
        </div>
```

Templates can read the `session` directly, so we check `session.username`. If someone is logged in we show a Logout link, otherwise we show Login and Register. It doesn't make sense to offer Logout to a visitor who was never logged in.

[Save the file](https://fmze.co/fftq-5.4.6).

Let's test the whole loop. Restart the app, register if you haven't, then log in. The navbar switches to Logout, proving the session is set. Click Logout and it flips back. We now have real accounts with real sessions, which is exactly what we need before users can start following each other in the next lesson.

## The Social Graph: Following Users <!-- 5.5 -->

A feed is only interesting if it's a feed of people you follow, so before we can build one, users need to be able to follow each other. In this lesson we'll model that relationship, and we'll also write our first custom decorator to protect the routes that change it.

Let's start with the decorator, because we're about to need it. Following someone should only be possible when you're logged in. We could check the session at the top of every protected view, but that gets repetitive fast. Instead we'll write a login_required decorator once and apply it wherever we need it.

![Instead of repeating the same session check at the top of every protected view, write the guard once as a decorator and apply it wherever it's needed.](images/5.5-scene2-img2.png)

![Following someone should only work when there's a session: a logged-out visitor is redirected to the login page and the view never runs.](images/5.5-scene2-img1.png)

Open `utils/helpers.py` and add the decorator. First extend the imports at the top:

{lang=python,line-numbers=on,starting-line-number=1}
```
from functools import wraps
from typing import Any, Callable, Optional

from quart import redirect, request, session, url_for
from sqlalchemy import select
from sqlalchemy.engine import Row

from user.models import user_table
```

Then add the decorator below `get_user_by_username`:

{lang=python,line-numbers=on,starting-line-number=17}
```
def login_required(f: Callable) -> Callable:
    @wraps(f)
    async def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if session.get("username") is None:
            return redirect(url_for("user_app.login", next=request.url))
        return await f(*args, **kwargs)

    return decorated_function
```

A decorator is a function that wraps another function to add behavior around it. Ours wraps a view: before the view runs, it checks the session, and if nobody's logged in, it redirects to the login page instead of running the view.

![A decorator wraps the view: it checks the session first, redirects to login if nobody is logged in, and only then awaits the real view.](images/5.5-scene2-img3.png)

There's one detail that's easy to get wrong in an async app. The wrapper, `decorated_function`, is itself declared `async`, and it awaits the real view. If we wrote a plain function that returned a coroutine, Quart wouldn't recognize it as a coroutine function and wouldn't await it properly. So the wrapper must be async too.

![The wrapper must be declared async and await the view, otherwise it just returns a coroutine that Quart never awaits.](images/5.5-scene2-img4.png)

[Save the file](https://fmze.co/fftq-5.5.1).

Now the model. We need to decide what a "follow" actually is. On Facebook, friendship is mutual: if we're friends, we both see each other. On Twitter, following is one directional: I can follow you without you following me back. We'll go with the Twitter style, because it's simpler and it's what a feed really needs.

![](images/5.5-scene4-img1.png)

![](images/5.5-scene4-img2.png)

Create a `relationship` folder with an empty `__init__.py`, and a `models.py` inside it:

{lang=python,line-numbers=on}
```
from sqlalchemy import Column, ForeignKey, Integer, Table

from db import metadata

# Unidirectional follow (Twitter-style): fm_user_id follows to_user_id.
relationship_table = Table(
    "relationship",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("fm_user_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("to_user_id", Integer, ForeignKey("user.id"), nullable=False),
)
```

This table is interesting because it points back at the `user` table twice. Each row is one follow: `fm_user_id` is the user doing the following (the "from" user), and `to_user_id` is the user being followed (the "to" user).

Both columns are foreign keys to `user.id`. A foreign key tells the database these values must be real user ids, so we can never have a follow that points at a user who doesn't exist. A single table referencing another table from two different columns like this is how you model a graph of connections between rows of the same kind.

[Save the file](https://fmze.co/fftq-5.5.2).

Now the views. Create `relationship/views.py`:

{lang=python,line-numbers=on}
```
from typing import List

from quart import Blueprint, abort, current_app, redirect, session, url_for
from quart_wtf import QuartForm
from sqlalchemy import delete, insert, select

from utils.helpers import get_user_by_username, login_required
from relationship.models import relationship_table

relationship_app = Blueprint("relationship_app", __name__)


class EmptyForm(QuartForm):
    """CSRF-only form used for the follow/unfollow POSTs (no visible fields)."""
```

We set up the blueprint and, right away, a form with no fields. Why a form for a follow button? Because following changes data, so it must be a `POST`, and every `POST` in our app is CSRF protected. `EmptyForm` has no visible inputs, but it still carries a CSRF token we can validate. It's the smallest possible protected form.

Next, two small query helpers in the same file:

{lang=python,line-numbers=on,starting-line-number=15}
```
async def is_following(conn, fm_user_id: int, to_user_id: int) -> bool:
    result = await conn.execute(
        select(relationship_table).where(
            (relationship_table.c.fm_user_id == fm_user_id)
            & (relationship_table.c.to_user_id == to_user_id)
        )
    )
    return result.fetchone() is not None


async def followers(conn, user_id: int) -> List[int]:
    """Return the list of user_ids following ``user_id`` (needed for post fan-out)."""
    result = await conn.execute(
        select(relationship_table.c.fm_user_id).where(
            relationship_table.c.to_user_id == user_id
        )
    )
    return [row.fm_user_id for row in result.fetchall()]
```

`is_following` answers a yes or no question: is there a row where this "from" user follows this "to" user? We use it to decide whether a profile shows a Follow or an Unfollow button.

`followers` returns the ids of everyone following a given user. We don't need it on screen yet, but keep it in mind: when someone posts, this is the exact list of people whose feeds that post should land in. It's the seed of the whole feed system.

Now the actions themselves, follow and unfollow:

{lang=python,line-numbers=on,starting-line-number=33}
```
@relationship_app.route("/follow/<username>", methods=["POST"])
@login_required
async def follow(username: str):
    form = await EmptyForm.create_form()
    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            target = await get_user_by_username(conn, username)
            if target is None:
                abort(404)

            my_id = session["user_id"]
            if target.id != my_id and not await is_following(conn, my_id, target.id):
                await conn.execute(
                    insert(relationship_table).values(
                        fm_user_id=my_id, to_user_id=target.id
                    )
                )

    return redirect(url_for("user_app.profile", username=username))
```

Here's the decorator paying off. We stack `@login_required` right under the route, and now this view simply can't run for a logged out visitor. Inside, we validate the CSRF token through `EmptyForm`, look up the target user, and 404 if there's no such person.

Then we insert the follow, but only if two things hold: you're not trying to follow yourself, and you're not already following them. That guard keeps the table clean and avoids duplicate rows. When we're done, we send you back to the profile you were looking at.

Unfollow is the reverse, a `delete` instead of an `insert`:

{lang=python,line-numbers=on,starting-line-number=54}
```
@relationship_app.route("/unfollow/<username>", methods=["POST"])
@login_required
async def unfollow(username: str):
    form = await EmptyForm.create_form()
    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            target = await get_user_by_username(conn, username)
            if target is None:
                abort(404)

            await conn.execute(
                delete(relationship_table).where(
                    (relationship_table.c.fm_user_id == session["user_id"])
                    & (relationship_table.c.to_user_id == target.id)
                )
            )

    return redirect(url_for("user_app.profile", username=username))
```

Same shape, same protection. We find the target user and delete the row where you follow them. If the row isn't there, the delete simply affects nothing, which is fine.

[Save the file](https://fmze.co/fftq-5.5.3).

Now register the blueprint. Open `application.py`, import `relationship_app`, and register it alongside `user_app`:

{lang=python,line-numbers=on,starting-line-number=8}
```
    from user.views import user_app
    from relationship.views import relationship_app

    app.register_blueprint(user_app)
    app.register_blueprint(relationship_app)
```

[Save the file](https://fmze.co/fftq-5.5.4).

Now tell Alembic about the new model. Open `migrations/env.py` and add the import next to the user one:

{lang=python,line-numbers=on,starting-line-number=17}
```
from relationship.models import relationship_table  # noqa: F401
```

[Save the file](https://fmze.co/fftq-5.5.5).

Now run the migration for the new table:

{lang=bash,line-numbers=off}
```
$ docker compose build web
$ docker compose run --rm web uv run alembic revision --autogenerate -m "create relationship table"
$ docker compose run --rm web uv run alembic upgrade head
```

The follow buttons live on a user's profile, and we don't have a profile page yet, so let's add a simple one. Open `user/views.py`. We'll need a few more imports here, plus our helpers and the relationship functions:

{lang=python,line-numbers=on,starting-line-number=16}
```
from utils.helpers import get_user_by_username, login_required
from relationship.models import relationship_table
from relationship.views import EmptyForm, is_following
```

Then add the profile view:

{lang=python,line-numbers=on,starting-line-number=70}
```
@user_app.route("/user/<username>")
async def profile(username: str) -> str:
    engine = current_app.dbc  # type: ignore
    async with engine.begin() as conn:
        profile_user = await get_user_by_username(conn, username)
        if profile_user is None:
            abort(404)

        my_user_id = session.get("user_id")
        if profile_user.id == my_user_id:
            relationship = "self"
        elif my_user_id is not None and await is_following(
            conn, my_user_id, profile_user.id
        ):
            relationship = "following"
        else:
            relationship = "not_following"

        followers_result = await conn.execute(
            select(relationship_table).where(
                relationship_table.c.to_user_id == profile_user.id
            )
        )
        follower_count = len(followers_result.fetchall())

    follow_form = await EmptyForm.create_form()

    return await render_template(
        "user/profile.html",
        profile_user=profile_user,
        relationship=relationship,
        follower_count=follower_count,
        follow_form=follow_form,
    )
```

We look up the user whose profile this is and 404 if they don't exist. Then we work out our relationship to them: is this my own profile, am I already following them, or not? That drives which button we show. We also count their followers with a quick query.

The one new-looking thing is `follow_form`. We create an `EmptyForm` and hand it to the template purely so the follow and unfollow buttons have a CSRF token to submit. We'll reuse this pattern every time a page has an action button.

[Save the file](https://fmze.co/fftq-5.5.6).

Finally the profile template. Create `templates/user/profile.html`:

{lang=html,line-numbers=on}
```
{% extends "base.html" %}

{% block title %}{{ profile_user.username }}{% endblock %}

{% block content %}

{% include "navbar.html" %}

<div class="row">
    <div class="col-md-8 offset-md-2">

        <h3>@{{ profile_user.username }}</h3>
        <p class="text-muted">{{ follower_count }} followers</p>

        {% if relationship == "following" %}
        <form method="POST" action="{{ url_for('relationship_app.unfollow', username=profile_user.username) }}">
            {{ follow_form.csrf_token }}
            <button type="submit" class="btn btn-outline-secondary">Unfollow</button>
        </form>
        {% elif relationship == "not_following" %}
        <form method="POST" action="{{ url_for('relationship_app.follow', username=profile_user.username) }}">
            {{ follow_form.csrf_token }}
            <button type="submit" class="btn btn-primary">Follow</button>
        </form>
        {% endif %}

    </div>
</div>

{% endblock %}
```

We show the username and follower count, then choose a button based on the relationship the view computed. If we're already following, we render an Unfollow form; if not, a Follow form; and if it's our own profile, we render neither. Each form carries the CSRF token from `follow_form`.

[Save the file](https://fmze.co/fftq-5.5.7).

Time to try it. Register a second user so you have two accounts. Log in as one, visit the other's profile at `/user/theirname`, and click Follow. The button flips to Unfollow and the follower count ticks up. You've just built a social graph. Next we'll make profiles worth visiting by adding avatars.

## Profiles and Avatar Uploads <!-- 5.6 -->

Our profiles work, but they're bare. In this lesson we'll let users edit their profile and upload an avatar, which means handling a real file upload and processing an image. This is the first time we're accepting a file instead of just text, so there's a bit to set up.

Processing images means resizing and cropping them, and for that we'll use Wand, a Python binding for ImageMagick. ImageMagick is a system library, so it has to be installed in the container, not just as a Python package. Let's handle both.

Open the `Dockerfile` and install ImageMagick right after the base image, before we install our Python packages:

{lang=docker,line-numbers=on,starting-line-number=1}
```
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick libmagickwand-dev \
    && rm -rf /var/lib/apt/lists/*
```

We update the package list, install ImageMagick and its development headers, then clean up the list to keep the image small. This is a common pattern: when a Python library wraps a system tool, you install the system tool in the Dockerfile.

[Save the file](https://fmze.co/fftq-5.6.1) and declare the Python side with `uv add`:

{lang=bash,line-numbers=off}
```
$ uv add --no-sync Wand
```

Uploaded files have to be saved somewhere, and served back from somewhere, so let's add a few settings for that. Open `.quartenv` and add the upload paths:

{lang=python,line-numbers=on,starting-line-number=9}
```
UPLOADS_FOLDER=static/uploads
IMAGES_FOLDER=static/uploads
IMAGE_URL=/static/uploads
```

[Save the file](https://fmze.co/fftq-5.6.2) and read them into `settings.py`:

{lang=python,line-numbers=on,starting-line-number=10}
```
UPLOADS_FOLDER = os.environ.get("UPLOADS_FOLDER", "static/uploads")
IMAGES_FOLDER = os.environ.get("IMAGES_FOLDER", "static/uploads")
IMAGE_URL = os.environ.get("IMAGE_URL", "/static/uploads")
```

`UPLOADS_FOLDER` is where files land on disk, and `IMAGE_URL` is the public path the browser uses to fetch them back. They point at the same `static/uploads` folder, which Quart already serves for us.

[Save the file](https://fmze.co/fftq-5.6.3).

An avatar is square, so when someone uploads a rectangular photo we need to crop it to a square and produce a few sizes: a small one for the feed, a larger one for the profile. Let's write that image logic in its own file. Create `utils/imaging.py`:

{lang=python,line-numbers=on}
```
import time
from pathlib import Path
from typing import List, Tuple, Union

from wand.image import Image

AVATAR_SIZES: List[Tuple[str, int]] = [("sm", 50), ("lg", 75), ("xlg", 200)]


def crop_center(image: Image) -> None:
    """Center-crop ``image`` to a square sized to its narrower dimension."""
    dst_landscape = 1 > image.width / image.height
    wh = image.width if dst_landscape else image.height
    image.crop(
        left=int((image.width - wh) / 2),
        top=int((image.height - wh) / 2),
        width=int(wh),
        height=int(wh),
    )
```

We define our three avatar sizes up front, each with a short name and a pixel dimension. Then `crop_center` takes a Wand image and crops it to a centered square, using the shorter side as the length so we never crop past the edges. This is what keeps faces roughly centered instead of chopped off.

Now the function that actually saves the avatar:

{lang=python,line-numbers=on,starting-line-number=22}
```
def thumbnail_process(
    blob: bytes,
    dest_dir: Union[str, Path],
    content_id: Union[str, int],
    sizes: List[Tuple[str, int]] = AVATAR_SIZES,
) -> int:
    """Square-crop ``blob`` and save one PNG per size. Returns the image_id."""
    image_id = int(time.time())
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    for name, size in sizes:
        with Image(blob=blob) as img:
            crop_center(img)
            img.sample(size, size)
            img.format = "png"
            img.save(filename=str(dest / f"{content_id}.{image_id}.{name}.png"))
    return image_id
```

This takes the raw uploaded bytes, the folder to write to, and the user's id. It picks an `image_id`, which is simply the current unix timestamp. For each size, it crops to a square, scales it down, and saves a PNG named with the user id, the timestamp, and the size, like `3.1783289480.lg.png`.

Why put a timestamp in the filename? Because it doubles as a cache buster. When someone uploads a new avatar, they get a new timestamp and therefore new filenames, so browsers can't show a stale cached image. The function returns that `image_id`, and we'll store it on the user row. A user with no avatar has no image id, and we'll show a default picture instead.

[Save the file](https://fmze.co/fftq-5.6.4).

For that to work, the `user` table needs a column to remember the avatar's image id. Open `user/models.py` and add an `image` column:

{lang=python,line-numbers=on,starting-line-number=10}
```
    Column("password", String(128)),
    # unix timestamp of the last uploaded avatar; NULL = default avatar
    Column("image", Integer, nullable=True),
)
```

It's a nullable integer holding that timestamp. Null means the user hasn't uploaded anything, so we fall back to the default avatar.

[Save the file](https://fmze.co/fftq-5.6.5) and migrate. Since we changed an existing table, Alembic will generate an `ALTER TABLE` that adds the column:

{lang=bash,line-numbers=off}
```
$ docker compose build web
$ docker compose run --rm web uv run alembic revision --autogenerate -m "add image to user"
$ docker compose run --rm web uv run alembic upgrade head
```

Now let's build the URL helper that turns a user's image id into a path the browser can load. Open `utils/helpers.py` and add:

{lang=python,line-numbers=on,starting-line-number=26}
```
async def get_user_by_id(conn: Any, user_id: int) -> Optional[Row]:
    result = await conn.execute(select(user_table).where(user_table.c.id == user_id))
    return result.fetchone()


def image_url(user_id: int, image: Optional[int], size: str = "lg") -> str:
    if image:
        return f"{current_app.config['IMAGE_URL']}/avatars/{user_id}.{image}.{size}.png"
    return "/static/default_profile.png"
```

We add `get_user_by_id`, the companion to our username lookup, because editing a profile means loading the current user by their session id. Then `image_url` builds the avatar path: if the user has an image id, it points at their uploaded file at the requested size; if not, it returns a default picture. Add `current_app` to the imports at the top of the file for this to work.

[Save the file](https://fmze.co/fftq-5.6.6). Drop a placeholder `default_profile.png` into the `static` folder so logged-out or avatar-less users still show something.

Editing a profile is a form with a file field, so we need a new form. Open `user/forms.py` and add it below `UserForm`:

{lang=python,line-numbers=on,starting-line-number=17}
```
class ProfileEditForm(QuartForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=15)])
    image = FileField(
        "Profile image",
        validators=[FileAllowed(["png", "jpg", "jpeg"], "Images only!")],
    )
```

This form has the username again, plus an `image` field. `FileField` is WTForms' file upload field, and `FileAllowed` is a validator that rejects anything that isn't a PNG or JPEG, with a friendly message. Add `FileAllowed` and `FileField` to the `quart_wtf` import at the top of the file.

[Save the file](https://fmze.co/fftq-5.6.7).

Now the profile edit view. This one is longer, so let's build it in pieces. Open `user/views.py` and start with the setup, importing what we need:

{lang=python,line-numbers=on,starting-line-number=1}
```
from pathlib import Path

from sqlalchemy import insert, select, update

from utils.helpers import (
    get_user_by_id,
    get_user_by_username,
    image_url,
    login_required,
)
from utils.imaging import thumbnail_process
from user.forms import ProfileEditForm, UserForm
```

We bring in `update` for changing the user row, our new helpers, and the `thumbnail_process` function. Now a tiny helper to keep the avatars in their own subfolder, and one to run the image processing:

{lang=python,line-numbers=on,starting-line-number=110}
```
def _avatars_dir() -> Path:
    return Path(current_app.config["UPLOADS_FOLDER"]) / "avatars"


def _save_avatar(file_storage, user_id: int) -> int:
    data = file_storage.read()
    return thumbnail_process(data, _avatars_dir(), user_id)
```

`_avatars_dir` points at `static/uploads/avatars`, and `_save_avatar` reads the uploaded file's bytes and hands them to `thumbnail_process`, returning the new image id. Now the edit view itself:

{lang=python,line-numbers=on,starting-line-number=119}
```
@user_app.route("/profile/edit", methods=["GET", "POST"])
@login_required
async def profile_edit() -> Union[str, Response]:
    form = await ProfileEditForm.create_form()
    error: Optional[str] = None
    engine = current_app.dbc  # type: ignore

    async with engine.begin() as conn:
        current_user = await get_user_by_id(conn, session["user_id"])

    if request.method == "GET":
        form.username.data = current_user.username

    if await form.validate_on_submit():
        new_username = form.username.data
        ts: Optional[int] = None
        if form.image.data:
            ts = _save_avatar(form.image.data, session["user_id"])

        async with engine.begin() as conn:
            values = {"username": new_username}
            if ts is not None:
                values["image"] = ts
            await conn.execute(
                update(user_table)
                .where(user_table.c.id == session["user_id"])
                .values(**values)
            )

        session["username"] = new_username
        await flash("Profile updated")
        return redirect(url_for(".profile", username=new_username))

    return await render_template(
        "user/profile_edit.html",
        form=form,
        avatar_url=image_url(current_user.id, current_user.image, "xlg"),
        error=error,
    )
```

The view is `login_required`, since you can only edit your own profile. We load the current user by their session id. On a `GET`, we pre-fill the username field so the form shows the existing name.

On a valid `POST`, we only process an image if one was actually uploaded, checking `form.image.data`. If there is one, `_save_avatar` crops and saves it and gives us a new timestamp. Then we build the update: always the username, and the new image id only if a file came in. We update the row, refresh the session username in case it changed, and redirect back to the profile.

Add `request` to the Quart imports for the `GET` check. Remember to import `Response` too if you removed it earlier.

[Save the file](https://fmze.co/fftq-5.6.8).

The edit page needs a template. Create `templates/user/profile_edit.html`:

{lang=html,line-numbers=on}
```
{% extends "base.html" %}

{% block title %}Edit profile{% endblock %}

{% block content %}

{% include "navbar.html" %}

<div class="row">
    <div class="col-md-6 offset-md-3">

        <h3>Edit profile</h3>

        <img src="{{ avatar_url }}" class="rounded-circle mb-3" width="120" height="120" alt="avatar">

        {% from "_formhelpers.html" import render_field %}

        <form method="POST" enctype="multipart/form-data">
            {{ render_field(form.username) }}
            {{ render_field(form.image) }}
            {{ form.csrf_token }}
            <button type="submit" class="btn btn-primary">Save</button>
        </form>

    </div>
</div>

{% endblock %}
```

We show the current avatar at the top, then the form. The one detail that matters for uploads is `enctype="multipart/form-data"` on the form tag. Without it, the browser sends only the text fields and drops the file. Any form with a file upload needs that attribute.

[Save the file](https://fmze.co/fftq-5.6.9).

Two small touches to finish. Add an avatar to the profile page by loading `image_url` in the profile view and showing it in `profile.html`, and add an Edit profile link to the navbar for the logged-in user. With those in place, restart the app, edit your profile, and upload a photo. It gets cropped to a neat circle avatar and shows up on your profile. Now that people can post as themselves, let's give them something to post.

## Posting: Messages, Images, and Permalinks <!-- 5.7 -->

It's time for the content itself. In this lesson we'll build posts: a message, an optional image, and a permanent, shareable address for each one. That address, the permalink, is worth getting right, so we'll design it carefully.

Let's start with the model. Create a `post` folder with an empty `__init__.py`, and a `models.py` inside:

{lang=python,line-numbers=on}
```
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)

from db import metadata

post_table = Table(
    "post",
    metadata,
    Column("id", Integer, primary_key=True),
    # Opaque, URL-safe id used in the SEO permalink (/post/<uid>/<slug>).
    Column("uid", String(16), nullable=False, unique=True, index=True),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("message", Text, nullable=False),
    Column("created", DateTime(timezone=True), server_default=func.now()),
)
```

A post has the usual `id`, a `user_id` foreign key to its author, and the `message` itself. We use `Text` rather than `String` because a post can be long and we don't want a length cap.

Two columns are new in spirit. The `created` column has a `server_default` of `func.now()`, which means Postgres stamps the creation time itself when we insert, so we never have to pass it. And there's a `uid`, a short opaque id we'll use in the post's public URL. We'll come back to why in a moment.

Posts can also carry images, and we want to be ready for more than one someday, so images get their own table. Add it below `post_table`:

{lang=python,line-numbers=on,starting-line-number=27}
```
post_image_table = Table(
    "post_image",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("post.id"), nullable=False),
    Column("image_id", Integer, nullable=False),
    Column("width", Integer, nullable=False),
    Column("position", Integer, nullable=False),
)
```

Each row is one image belonging to a post, with the same timestamp `image_id` trick we used for avatars, plus its scaled `width` and a `position` so multiple images keep their order. In the interface we'll allow one image per post, but the storage is ready for more.

[Save the file](https://fmze.co/fftq-5.7.1).

Now those two URL pieces, the `uid` and the slug. Let's add both helpers to `utils/helpers.py`:

{lang=python,line-numbers=on,starting-line-number=1}
```
import re
import secrets
import string
```

{lang=python,line-numbers=on,starting-line-number=40}
```
_UID_ALPHABET = string.ascii_lowercase + string.digits


def generate_uid(length: int = 8) -> str:
    """Return a short, opaque, URL-safe id for a post permalink."""
    return "".join(secrets.choice(_UID_ALPHABET) for _ in range(length))


def slugify(text: str, max_words: int = 6, max_len: int = 60) -> str:
    """Turn a post message into an SEO-friendly URL slug."""
    words = re.sub(r"[^a-z0-9\s-]", "", (text or "").lower()).split()
    slug = "-".join(words[:max_words])[:max_len].strip("-")
    return slug or "post"
```

Here's the design. A permalink like `/post/ab12cd34/i-need-to-go-to-the-supermarket` has two parts. The `uid`, generated by `generate_uid`, is a short random string of letters and digits. It's what actually identifies the post, and being random and opaque means people can't guess how many posts exist or walk through them by incrementing a number.

The second part is the slug, made by `slugify` from the message: lowercased, stripped of punctuation, and cut to the first few words. The slug is purely cosmetic, there for readability and search engines. Only the `uid` matters for lookup, which lets us do a neat trick later: if the slug in the URL is stale or missing, we redirect to the correct one.

[Save the file](https://fmze.co/fftq-5.7.2).

Post images keep their aspect ratio but are scaled to a fixed height so several could sit side by side neatly. That's a different transform than the square crop we used for avatars, so let's add it to `utils/imaging.py`:

{lang=python,line-numbers=on,starting-line-number=38}
```
def image_height_transform(
    blob: bytes,
    dest_dir: Union[str, Path],
    content_id: Union[str, int],
    height: int = 200,
) -> Tuple[int, int]:
    """Scale ``blob`` to a fixed ``height`` (aspect kept). Returns (image_id, width)."""
    image_id = int(time.time())
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    with Image(blob=blob) as img:
        img.transform(resize=f"x{height}")
        img.format = "png"
        img.save(filename=str(dest / f"{content_id}.{image_id}.xlg.png"))
        return image_id, img.width
```

It's the same Wand pattern as before, but instead of cropping to a square, `transform(resize="x200")` scales the image to two hundred pixels tall and keeps the width proportional. It returns both the image id and the resulting width, which we store so the layout knows how much room to leave.

[Save the file](https://fmze.co/fftq-5.7.3).

The post form is short. Create `post/forms.py`:

{lang=python,line-numbers=on}
```
from quart_wtf import FileAllowed, FileField, QuartForm
from wtforms import TextAreaField
from wtforms.validators import DataRequired, Length


class PostForm(QuartForm):
    message = TextAreaField(
        "What's on your mind?",
        validators=[DataRequired(), Length(max=500)],
    )
    image = FileField(
        "Photo",
        validators=[FileAllowed(["png", "jpg", "jpeg"], "Images only!")],
    )
```

A required message limited to five hundred characters, and an optional image with the same image-only validation we used for avatars. Nothing new here, which is the point: once you know quart-wtforms, every form looks like this.

[Save the file](https://fmze.co/fftq-5.7.4).

Now the views. Create `post/views.py` with the imports and blueprint:

{lang=python,line-numbers=on}
```
from pathlib import Path
from typing import Optional

from quart import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    session,
    url_for,
)
from sqlalchemy import insert, select

from utils.helpers import generate_uid, login_required, post_image_url, slugify
from utils.imaging import image_height_transform
from post.forms import PostForm
from post.models import post_image_table, post_table

post_app = Blueprint("post_app", __name__)


def _posts_dir() -> Path:
    return Path(current_app.config["UPLOADS_FOLDER"]) / "posts"
```

We import our new helpers and the fixed-height transform, and add a `_posts_dir` helper pointing at where post images are stored, mirroring the avatars folder. Add a small `post_image_url` helper to `utils/helpers.py` too, building the URL for a post image the same way `image_url` does for avatars.

Now the home page, which shows the post form. For now it just lists your own recent posts so we have something to look at; next lesson it becomes the real feed:

{lang=python,line-numbers=on,starting-line-number=24}
```
@post_app.route("/")
async def home():
    if session.get("username") is None:
        return redirect(url_for("user_app.login"))

    form = await PostForm.create_form()
    engine = current_app.dbc  # type: ignore
    async with engine.begin() as conn:
        posts = (
            await conn.execute(
                select(post_table)
                .where(post_table.c.user_id == session["user_id"])
                .order_by(post_table.c.created.desc())
                .limit(10)
            )
        ).fetchall()

    return await render_template("post/home.html", posts=posts, form=form)
```

If nobody's logged in we send them to login. Otherwise we build an empty `PostForm` for the "what's on your mind" box and load the current user's ten most recent posts, newest first. That's a placeholder for the feed we'll build next.

Now the view that actually creates a post:

{lang=python,line-numbers=on,starting-line-number=43}
```
@post_app.route("/post", methods=["POST"])
@login_required
async def create_post():
    form = await PostForm.create_form()

    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            result = await conn.execute(
                insert(post_table).values(
                    uid=generate_uid(),
                    user_id=session["user_id"],
                    message=form.message.data,
                )
            )
            post_id = result.inserted_primary_key[0]

            if form.image.data:
                image_id, width = image_height_transform(
                    form.image.data.read(), _posts_dir(), post_id
                )
                await conn.execute(
                    insert(post_image_table).values(
                        post_id=post_id, image_id=image_id, width=width, position=0
                    )
                )

    return redirect(url_for(".home"))
```

We validate the form, then insert the post with a freshly generated `uid`, the author's id, and the message. We grab the new post's id from `inserted_primary_key` because we'll need it if there's an image.

If a photo was uploaded, we run it through `image_height_transform` and record a `post_image` row pointing at the post. Then we redirect home. Simple for now; we'll layer fan-out and live delivery on top of this exact function over the next two lessons.

Finally, the permalink page. This is where that `uid` and slug design pays off:

{lang=python,line-numbers=on,starting-line-number=70}
```
@post_app.route("/post/<uid>/")
@post_app.route("/post/<uid>/<slug>")
@login_required
async def detail(uid: str, slug: Optional[str] = None):
    engine = current_app.dbc  # type: ignore
    async with engine.begin() as conn:
        post = (
            await conn.execute(select(post_table).where(post_table.c.uid == uid))
        ).fetchone()

    if post is None:
        abort(404)

    canonical_slug = slugify(post.message)
    if slug != canonical_slug:
        return redirect(
            url_for("post_app.detail", uid=uid, slug=canonical_slug), code=301
        )

    form = await PostForm.create_form()
    return await render_template("post/detail.html", post=post, form=form)
```

We look the post up by its `uid` alone, ignoring the slug, and 404 if there's no such post. Then we compute what the slug should be from the current message. If the URL's slug doesn't match, we issue a `301` redirect to the canonical URL.

That redirect is the trick. It means every post has exactly one correct address that search engines will index, no matter what slug someone typed or linked. A stale slug still finds the post and then bounces to the right URL.

[Save the file](https://fmze.co/fftq-5.7.5).

Register the blueprint in `application.py` and import the two new models in `migrations/env.py`, the same two-step dance as before. Then create the home and detail templates with the post form and a simple card for each post, and run the migration for the `post` and `post_image` tables:

{lang=bash,line-numbers=off}
```
$ docker compose build web
$ docker compose run --rm web uv run alembic revision --autogenerate -m "create post and post_image tables"
$ docker compose run --rm web uv run alembic upgrade head
```

Restart the app, write a post, attach a photo. It shows up on your home page with its image scaled to a tidy height, and clicking its timestamp takes you to its permalink. We have content. Now let's make it flow between users.

## The Feed: Fan-out on Write <!-- 5.8 -->

Right now your home page shows only your own posts. A social feed shows posts from everyone you follow, newest activity first. In this lesson we'll build that, and the way we build it is the most important architectural idea in the whole chapter, so let's think about it before we code.

There are two ways to build a feed. The obvious one is to query it on read: every time you open your home page, look up everyone you follow, then fetch their recent posts and merge them. That works, but it gets slow as people follow more accounts, because every page load does a big, expensive query.

The approach real feeds use is the opposite: fan-out on write. The moment someone posts, we immediately write one row into a `feed` table for each of their followers. Reading your feed then becomes a simple, fast lookup of your own rows. We do a little more work when someone posts, which is rare, to make reading, which is constant, cheap. That's the trade we want.

So we need a `feed` table. It's a materialized, per-user timeline: each row says "this post belongs in this user's feed". Add it to `post/models.py` below `post_table`:

{lang=python,line-numbers=on,starting-line-number=27}
```
feed_table = Table(
    "feed",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("post_id", Integer, ForeignKey("post.id"), nullable=False),
    Column("updated", DateTime(timezone=True), server_default=func.now()),
)
```

The key thing to understand is `user_id` here is not the author. It's the feed's owner, the recipient. One post by a popular user creates many feed rows, one per follower, each with that follower as `user_id`. The `updated` column is what we sort a feed by, so the freshest activity floats to the top.

[Save the file](https://fmze.co/fftq-5.8.1) and now let's write the fan-out logic in its own file. Create `utils/feed_ops.py`:

{lang=python,line-numbers=on}
```
from typing import Iterable

from sqlalchemy import insert

from post.models import feed_table


async def add_to_feed(conn, user_id: int, post_id: int) -> None:
    """Insert one feed row for a recipient."""
    await conn.execute(
        insert(feed_table).values(user_id=user_id, post_id=post_id)
    )


async def fan_out_post(conn, post_id: int, recipient_ids: Iterable[int]) -> None:
    """A brand-new post lands directly in the author's + followers' feeds."""
    for user_id in set(recipient_ids):
        await add_to_feed(conn, user_id, post_id)
```

`add_to_feed` writes a single feed row, and `fan_out_post` loops over a set of recipients and writes one for each. We wrap the recipients in `set()` so nobody gets a duplicate row. This is the whole fan-out engine, and we'll extend it in a couple of lessons when comments start bubbling posts around.

[Save the file](https://fmze.co/fftq-5.8.2).

Now wire it into `create_post`. Import the helpers at the top of `post/views.py`:

{lang=python,line-numbers=on,starting-line-number=15}
```
from utils.feed_ops import fan_out_post
from relationship.views import followers
```

Then, right after we insert the post and get its `post_id`, fan it out:

{lang=python,line-numbers=on,starting-line-number=58}
```
            recipient_ids = set(await followers(conn, session["user_id"]))
            recipient_ids.add(session["user_id"])
            await fan_out_post(conn, post_id, recipient_ids)
```

Remember the `followers` helper we wrote back in the relationship lesson, and said to keep in mind? This is the moment. We fetch everyone who follows the author, add the author themselves so your own posts show in your own feed, and fan the post out to all of them. Every one of those users now has a feed row for this post.

[Save the file](https://fmze.co/fftq-5.8.3).

Now the home page reads from the feed instead of the author's own posts. This query joins three tables, so let's replace the `home` view's query:

{lang=python,line-numbers=on,starting-line-number=30}
```
        feed_query = (
            select(
                post_table.c.id.label("post_id"),
                post_table.c.uid,
                post_table.c.message,
                post_table.c.created,
                user_table.c.username.label("author_username"),
                user_table.c.image.label("author_image"),
                user_table.c.id.label("author_id"),
            )
            .select_from(
                feed_table.join(post_table, feed_table.c.post_id == post_table.c.id)
                .join(user_table, post_table.c.user_id == user_table.c.id)
            )
            .where(feed_table.c.user_id == session["user_id"])
            .order_by(feed_table.c.updated.desc())
            .limit(10)
        )
        posts = (await conn.execute(feed_query)).fetchall()
```

We start from `feed_table` and keep only the rows where the feed owner is us. Then we join to `post_table` to get each post's content, and join again to `user_table` to get the author's name and avatar. We order by the feed's `updated` column so the newest activity is on top, and take the first ten. Add `user_table` to the imports for the join.

[Save the file](https://fmze.co/fftq-5.8.4).

One page of ten posts isn't enough for an active feed, so let's add infinite scroll: when you reach the bottom, load the next page. That means an endpoint that returns just the next batch of post cards. Add a `feed` view:

{lang=python,line-numbers=on,starting-line-number=52}
```
@post_app.route("/feed")
@login_required
async def feed():
    try:
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0

    engine = current_app.dbc  # type: ignore
    async with engine.begin() as conn:
        posts = await _load_feed(conn, session["user_id"], offset=offset)

    return await render_template("post/_feed_items.html", posts=posts)
```

This takes an `offset` from the query string and returns the next slice of the feed, rendered with a small partial template, `_feed_items.html`, that loops over posts and renders each card. Pull the feed query we just wrote into a shared `_load_feed` helper so both `home` and `feed` use it, differing only by their offset. Add `request` to the imports.

[Save the file](https://fmze.co/fftq-5.8.5). On the front end, a little script watches for the page bottom and fetches the next offset. Create `static/js/infinite_scroll.js`:

{lang=javascript,line-numbers=on}
```
document.addEventListener("DOMContentLoaded", () => {
  const feed = document.getElementById("feed");
  const sentinel = document.getElementById("feed-sentinel");
  if (!feed || !sentinel) return;

  let offset = feed.querySelectorAll("[data-post-id]").length;
  let loading = false;
  let done = false;

  const observer = new IntersectionObserver(async (entries) => {
    if (!entries[0].isIntersecting || loading || done) return;
    loading = true;
    const res = await fetch(`/feed?offset=${offset}`);
    const html = (await res.text()).trim();
    if (!html) {
      done = true;
    } else {
      feed.insertAdjacentHTML("beforeend", html);
      offset = feed.querySelectorAll("[data-post-id]").length;
    }
    loading = false;
  });

  observer.observe(sentinel);
});
```

We use an `IntersectionObserver`, the browser's efficient way to notice when an element scrolls into view. We watch an empty sentinel element at the bottom of the feed. When it becomes visible, we fetch the next page by offset and append the returned cards. If the server returns nothing, we're at the end and we stop asking.

[Save the file](https://fmze.co/fftq-5.8.6) and load it from the home template, adding a `<div id="feed-sentinel"></div>` after the feed. Rebuild, run the migration for the `feed` table, then restart. Log in as two accounts, follow one from the other, and post. The post now appears in the follower's home feed, and scrolling loads older posts. The feed works, but you still have to refresh to see new posts. Let's fix that with SSE.

## Going Live: the SSE Broker and EventSource Client <!-- 5.9 -->

This is the lesson the whole chapter has been building toward. We have a feed that fills in when you refresh; now we'll make new posts appear the instant they're written, using the Server Sent Events we introduced at the very start. Time to make that promise real.

There are two halves to this: the server pushing events, and the browser receiving them. Let's build the server side first, starting with a tiny class that formats an event in the SSE wire format. Create `utils/sse.py`:

{lang=python,line-numbers=on}
```
import asyncio
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class ServerSentEvent:
    data: str
    event: Optional[str] = None  # "post" | "comment" | "like"
    id: Optional[str] = None

    def encode(self) -> bytes:
        msg = f"data: {self.data}\n"
        if self.event is not None:
            msg = f"event: {self.event}\n{msg}"
        if self.id is not None:
            msg = f"id: {self.id}\n{msg}"
        return (msg + "\n").encode("utf-8")
```

Remember from the intro that an SSE message is just text with `data:`, an optional `event:` type, and an optional `id:`, ending in a blank line. This little dataclass holds those three fields and its `encode` method builds exactly that text. Our event types will be `post`, `comment`, and `like`, just as we planned.

Now the broker, the piece that keeps track of who's connected and delivers events to the right people. Add it to the same file:

{lang=python,line-numbers=on,starting-line-number=20}
```
class Broker:
    """Routes Server-Sent Events to connected clients, keyed by user id."""

    def __init__(self) -> None:
        self.connections: dict[int, set[asyncio.Queue]] = {}

    async def publish(self, user_id: int, event: ServerSentEvent) -> None:
        for q in list(self.connections.get(user_id, ())):
            await q.put(event)

    async def publish_many(
        self, user_ids: Iterable[int], event: ServerSentEvent
    ) -> None:
        for user_id in set(user_ids):
            await self.publish(user_id, event)

    def subscribe(self, user_id: int) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self.connections.setdefault(user_id, set()).add(q)
        return q

    def unsubscribe(self, user_id: int, q: asyncio.Queue) -> None:
        conns = self.connections.get(user_id)
        if conns is not None:
            conns.discard(q)
            if not conns:
                self.connections.pop(user_id, None)


broker = Broker()
```

The broker keeps a dictionary from user id to a set of queues, one queue per open browser tab that user has. When someone opens the feed, they `subscribe` and get a queue. When we `publish` to a user, we drop the event into every queue they have open.

The important design decision is that the broker is keyed by user id, not global. We deliver an event only to the specific recipients it's meant for, exactly the same people who got a feed row. If we broadcast every post to everyone, users would briefly see posts from people they don't follow, which would then vanish on refresh. Per-user delivery mirrors the feed, so live and refreshed always agree.

Now the streaming endpoint. This is what the browser connects to. Add it to `post/views.py`:

{lang=python,line-numbers=on,starting-line-number=80}
```
@post_app.route("/sse")
@login_required
async def sse():
    user_id = session["user_id"]

    async def gen():
        q = broker.subscribe(user_id)
        try:
            while True:
                event = await q.get()
                yield event.encode()
        except asyncio.CancelledError:
            broker.unsubscribe(user_id, q)
            raise

    response = await make_response(
        gen(),
        {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
        },
    )
    response.timeout = None
    return response
```

We capture the user's id, then define an async generator `gen`. It subscribes to the broker and then loops forever, waiting for the next event on its queue and yielding the encoded bytes. Because it's a generator, Quart streams each yielded chunk to the browser as it arrives, keeping the connection open.

The headers make it a stream: `text/event-stream` is the SSE content type, and we turn off caching and buffering. When the browser closes the tab, the generator is cancelled, and we catch that to unsubscribe cleanly. And crucially we set `response.timeout = None`, because this response is meant to stay open forever, not time out like a normal request. Add `make_response` and `asyncio` to the imports.

[Save the file](https://fmze.co/fftq-5.9.1).

Now we publish an event when a post is created. Back in `create_post`, after the fan-out, build a payload and push it to the same recipients. Add the imports and the publish call:

{lang=python,line-numbers=on,starting-line-number=17}
```
import json

from utils.sse import ServerSentEvent, broker
from utils.helpers import image_url
```

{lang=python,line-numbers=on,starting-line-number=62}
```
        payload = {
            "post_id": post_id,
            "message": form.message.data,
            "author_username": session["username"],
            "avatar_url": image_url(session["user_id"], None, "sm"),
            "permalink": url_for(
                "post_app.detail", uid=post_uid, slug=slugify(form.message.data)
            ),
        }
        await broker.publish_many(
            recipient_ids,
            ServerSentEvent(event="post", data=json.dumps(payload)),
        )
```

We build a small dictionary describing the post, everything the browser needs to render a card, and serialize it to JSON. Then we `publish_many` to `recipient_ids`, the exact same set we just fanned the post out to. So the live push and the stored feed always reach the same people. Note we pass `event="post"`, which the browser will listen for by name.

[Save the file](https://fmze.co/fftq-5.9.2).

Now the browser side. We connect to `/sse` with the built-in `EventSource` object and render incoming posts. Create `static/js/broadcast.js`:

{lang=javascript,line-numbers=on}
```
document.addEventListener("DOMContentLoaded", () => {
  const feed = document.getElementById("feed");
  if (!feed) return;

  const es = new EventSource("/sse");

  const escapeHtml = (str) =>
    String(str).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));

  es.addEventListener("post", (e) => {
    const post = JSON.parse(e.data);
    if (feed.querySelector(`[data-post-id="${post.post_id}"]`)) return;

    const card = document.createElement("div");
    card.className = "card mb-3";
    card.setAttribute("data-post-id", post.post_id);
    card.innerHTML = `
      <div class="card-body">
        <a href="/user/${encodeURIComponent(post.author_username)}" class="fw-bold">@${escapeHtml(post.author_username)}</a>
        <p class="mb-1">${escapeHtml(post.message)}</p>
        <a href="${post.permalink}" class="small text-muted">permalink</a>
      </div>`;
    feed.prepend(card);
  });
});
```

We open an `EventSource` pointed at `/sse`. That one line does all the connection work: it opens the stream, keeps it alive, and even reconnects automatically if the network drops. Then we listen for our named `post` event.

When a post event arrives, we parse the JSON and build a card. We use a template literal, the JavaScript string with backticks and `${}` placeholders, to assemble the HTML, and `prepend` it to the top of the feed. This is the template-literal rendering the intro mentioned: no framework, just building a string and inserting it. We escape the text first so a post can't inject HTML, and we skip the card if it's already on the page, which guards against duplicates.

[Save the file](https://fmze.co/fftq-5.9.3) and load it from the home template inside the `scripts` block, alongside the infinite scroll script.

Now the moment of truth. Open two browsers, or a normal and a private window, and log in as two users who follow each other. Put their home pages side by side and post from one. The post appears on the other's feed instantly, with no refresh. That's Server Sent Events doing exactly what we promised at the start of the chapter. From here it's all engagement: comments and likes.

## Comments and Feed Bubbling <!-- 5.10 -->

Now let's let people reply. Comments are straightforward on their own, but they give us a chance to build one of FriendFeed's signature behaviors, and the reason it felt so alive: when someone you follow comments on a post, that post surfaces in your feed even if you don't follow the original author. We'll call that bubbling, and it's the interesting part of this lesson.

First the comment itself. Create a `comment` folder with an empty `__init__.py` and a `models.py`:

{lang=python,line-numbers=on}
```
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table, Text, func

from db import metadata

comment_table = Table(
    "comment",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("post.id"), nullable=False),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("comment", Text, nullable=False),
    Column("created", DateTime(timezone=True), server_default=func.now()),
)
```

Nothing surprising: a comment belongs to a post and an author, holds some text, and stamps its own creation time. Add a matching `CommentForm` in a `comment/forms.py` with a single required text field, exactly like our post form.

[Save the file](https://fmze.co/fftq-5.10.1).

Now for bubbling, and this is where the feed table needs two new columns. When a post appears in your feed because a friend commented on it, we want to show why: "Robert Scoble commented on this". So the feed row needs to record the reason. Update `feed_table` in `post/models.py`:

{lang=python,line-numbers=on,starting-line-number=27}
```
feed_table = Table(
    "feed",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("post_id", Integer, ForeignKey("post.id"), nullable=False),
    Column("updated", DateTime(timezone=True), server_default=func.now()),
    Column("reason_user_id", Integer, ForeignKey("user.id"), nullable=True),
    Column("reason_type", String(16), nullable=True),  # e.g. "comment"
    UniqueConstraint("user_id", "post_id", name="uq_feed_user_post"),
)
```

We add `reason_user_id`, who caused the post to bubble, and `reason_type`, what they did, like "comment". Both are nullable, because a post that's in your feed from a plain follow has no special reason.

The other addition is the `UniqueConstraint` on `user_id` and `post_id` together. This says a post can appear at most once in any given feed. That matters now, because a post could reach your feed two ways at once: you follow the author, and a friend also comments on it. Without the constraint we'd get a duplicate row. Add `String` and `UniqueConstraint` to the imports.

[Save the file](https://fmze.co/fftq-5.10.2) and migrate to add the columns and the constraint:

{lang=bash,line-numbers=off}
```
$ docker compose build web
$ docker compose run --rm web uv run alembic revision --autogenerate -m "feed bubbling: reason columns and unique"
$ docker compose run --rm web uv run alembic upgrade head
```

Now that a post can arrive by two routes, our simple "insert a feed row" isn't safe anymore. We need it to insert if the row is new, but just refresh the timestamp if it already exists. Postgres has exactly that: an upsert. Rewrite `utils/feed_ops.py`:

{lang=python,line-numbers=on}
```
from typing import Iterable, Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from post.models import feed_table


async def add_to_feed(
    conn,
    user_id: int,
    post_id: int,
    reason_user_id: Optional[int] = None,
    reason_type: Optional[str] = None,
) -> None:
    stmt = pg_insert(feed_table).values(
        user_id=user_id,
        post_id=post_id,
        reason_user_id=reason_user_id,
        reason_type=reason_type,
    )
    stmt = stmt.on_conflict_do_update(
        constraint="uq_feed_user_post",
        set_={"updated": func.now()},
    )
    await conn.execute(stmt)


async def fan_out_post(conn, post_id: int, recipient_ids: Iterable[int]) -> None:
    for user_id in set(recipient_ids):
        await add_to_feed(conn, user_id, post_id)


async def bubble_post(
    conn, post_id: int, recipient_ids: Iterable[int], reason_user_id: int, reason_type: str
) -> None:
    for user_id in set(recipient_ids):
        await add_to_feed(conn, user_id, post_id, reason_user_id, reason_type)
```

We switch to Postgres's own `insert` so we can chain `on_conflict_do_update`. Now if a feed row for this user and post already exists, instead of failing on the unique constraint, we bump its `updated` timestamp, which floats the post back to the top. That's exactly what we want: fresh activity, no duplicates.

`fan_out_post` is unchanged in spirit, and the new `bubble_post` is its sibling: it adds a post to feeds and records the reason it bubbled. Same machinery, one carries attribution.

[Save the file](https://fmze.co/fftq-5.10.3).

Now the comment view ties it together. Create `comment/views.py`:

{lang=python,line-numbers=on}
```
import json

from quart import Blueprint, current_app, redirect, session, url_for
from sqlalchemy import insert, select

from comment.forms import CommentForm
from comment.models import comment_table
from utils.feed_ops import bubble_post
from utils.helpers import login_required
from post.models import feed_table
from relationship.views import followers
from utils.sse import ServerSentEvent, broker

comment_app = Blueprint("comment_app", __name__)


@comment_app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
async def create_comment(post_id: int):
    form = await CommentForm.create_form()

    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            result = await conn.execute(
                insert(comment_table).values(
                    post_id=post_id,
                    user_id=session["user_id"],
                    comment=form.comment.data,
                )
            )
            comment_id = result.inserted_primary_key[0]

            # Bubble the post into my followers' feeds, tagged "<me> commented".
            follower_ids = await followers(conn, session["user_id"])
            recipients = set(follower_ids)
            recipients.add(session["user_id"])
            await bubble_post(conn, post_id, recipients, session["user_id"], "comment")

            # Everyone who now has this post in their feed should get the comment.
            feed_owner_ids = [
                r.user_id
                for r in (
                    await conn.execute(
                        select(feed_table.c.user_id).where(
                            feed_table.c.post_id == post_id
                        )
                    )
                ).fetchall()
            ]

        payload = {
            "post_id": post_id,
            "comment_id": comment_id,
            "comment": form.comment.data,
            "author_username": session["username"],
        }
        await broker.publish_many(
            feed_owner_ids,
            ServerSentEvent(event="comment", data=json.dumps(payload)),
        )

    return redirect(url_for("post_app.home"))
```

We insert the comment, then bubble the post to our followers plus ourselves, tagging the reason as "comment". Thanks to the upsert, followers who already had the post just see it move up; those who didn't get it now.

Then we ask the feed table who currently has this post, which now includes the freshly bubbled followers, and publish the `comment` event live to exactly those people. So the comment appears in real time on every feed showing that post, and nowhere else.

[Save the file](https://fmze.co/fftq-5.10.4). Register the `comment_app` blueprint, import the comment model in `migrations/env.py`, and add a `comment` event listener to `broadcast.js` that finds the post card by its id and appends the comment text. Restart, and now a comment from someone you follow makes their friend's post pop into your feed, tagged with who commented, live.

## Likes and Live Reactions <!-- 5.11 -->

The last piece of engagement is the like, and it teaches one more idea: making an action idempotent, so clicking Like and Unlike can be the same button toggling on and off, with the database keeping things consistent.

The model uses a unique constraint to enforce that. Create a `like` folder with an empty `__init__.py` and `models.py`:

{lang=python,line-numbers=on}
```
from sqlalchemy import Column, ForeignKey, Integer, Table, UniqueConstraint

from db import metadata

like_table = Table(
    "like",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("post.id"), nullable=False),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False),
    UniqueConstraint("post_id", "user_id", name="uq_like_post_user"),
)
```

The unique constraint on `post_id` and `user_id` guarantees one like per person per post. You can't accidentally like the same post twice, and that makes a like a clean on-off toggle rather than a counter we have to babysit.

[Save the file](https://fmze.co/fftq-5.11.1) and migrate as usual, remembering to import the model in `migrations/env.py`.

Now the toggle view. Create `like/views.py`:

{lang=python,line-numbers=on}
```
import json

from quart import Blueprint, current_app, redirect, session, url_for
from quart_wtf import QuartForm
from sqlalchemy import delete, func, insert, select

from utils.helpers import login_required
from like.models import like_table
from post.models import feed_table
from user.models import user_table
from utils.sse import ServerSentEvent, broker

like_app = Blueprint("like_app", __name__)


class LikeForm(QuartForm):
    """CSRF-only form for the like toggle POST."""


@like_app.route("/like/<int:post_id>", methods=["POST"])
@login_required
async def toggle_like(post_id: int):
    form = await LikeForm.create_form()

    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            existing = (
                await conn.execute(
                    select(like_table).where(
                        (like_table.c.post_id == post_id)
                        & (like_table.c.user_id == session["user_id"])
                    )
                )
            ).fetchone()

            if existing is not None:
                await conn.execute(delete(like_table).where(like_table.c.id == existing.id))
            else:
                await conn.execute(
                    insert(like_table).values(post_id=post_id, user_id=session["user_id"])
                )

            likers = [
                r.username
                for r in (
                    await conn.execute(
                        select(user_table.c.username)
                        .select_from(
                            like_table.join(user_table, like_table.c.user_id == user_table.c.id)
                        )
                        .where(like_table.c.post_id == post_id)
                        .order_by(like_table.c.id.asc())
                    )
                ).fetchall()
            ]

            feed_owner_ids = [
                r.user_id
                for r in (
                    await conn.execute(
                        select(feed_table.c.user_id).where(feed_table.c.post_id == post_id)
                    )
                ).fetchall()
            ]

        await broker.publish_many(
            feed_owner_ids,
            ServerSentEvent(
                event="like",
                data=json.dumps({"post_id": post_id, "likers": likers}),
            ),
        )

    return redirect(url_for("post_app.home"))
```

It's a toggle. We look for an existing like from this user on this post. If there is one, we delete it; if not, we insert one. The same button, the same route, both directions. Then we gather the current list of likers, newest activity aside, ordered by when they liked.

Finally we push a `like` event to everyone who has the post in their feed, carrying the updated list of names so their pages can re-render the likes line live. Same targeted delivery as comments.

[Save the file](https://fmze.co/fftq-5.11.2).

FriendFeed had a nice touch: instead of a bare count, it wrote out "Alice, Bob and Carol liked this", and collapsed the list once it got long. Let's build that line as a helper in `utils/helpers.py`:

{lang=python,line-numbers=on,starting-line-number=60}
```
def likes_line(likers, head: int = 3, collapse_over: int = 5) -> str:
    n = len(likers)
    if n == 0:
        return ""
    if n <= collapse_over:
        if n == 1:
            return f"{likers[0]} liked this"
        return ", ".join(likers[:-1]) + f" and {likers[-1]} liked this"
    shown = ", ".join(likers[:head])
    return f"{shown} and {n - head} other people liked this"
```

If nobody liked it, we show nothing. Up to five names, we list them all with a natural "and" before the last. Beyond that, we show the first three and collapse the rest into "and N other people liked this", so a wildly popular post doesn't print a hundred names. Render this line under each post, and add a `like` listener to `broadcast.js` that replaces it when a like event arrives.

[Save the file](https://fmze.co/fftq-5.11.3). Restart and try it. Like a post and the line updates; like it from another account and watch the names change live on the first. Unlike and it ticks back down. QuartFeed is now a complete, real-time social feed. All that's left is to make sure it stays that way.

## Testing the Live Feed <!-- 5.12 -->

We've built a lot, and every piece of it can break as we keep developing. We tested the counter app back in chapter four, so the fixtures will feel familiar; what's new here is testing things we couldn't before: forms with CSRF, logged-in sessions, and the fan-out that happens behind the scenes when someone posts.

Our tests hit forms, and every form has a CSRF token. In a test we don't want to fetch and echo tokens, so we simply turn CSRF off for the test app. Remember that `WTF_CSRF_ENABLED` setting we added: our `create_app` already takes config overrides, so we pass it as `False`. Start with a `conftest.py` in a `tests` folder, reusing the fresh-database fixture pattern from the counter app, and make sure it imports every model so `metadata.create_all` builds all our tables:

{lang=python,line-numbers=on,starting-line-number=1}
```
from user.models import user_table  # noqa: F401
from relationship.models import relationship_table  # noqa: F401
from post.models import feed_table, post_image_table, post_table  # noqa: F401
from comment.models import comment_table  # noqa: F401
from like.models import like_table  # noqa: F401
```

Then in the app fixture, add `WTF_CSRF_ENABLED=False` to the overrides passed into `create_app`, right alongside the test database settings. With CSRF off, our tests can post forms without wrestling with tokens.

[Save the file](https://fmze.co/fftq-5.12.1).

Let's test registration and login first. Create `tests/test_user.py`:

{lang=python,line-numbers=on}
```
import pytest


@pytest.mark.asyncio
async def test_register_and_login(create_test_client):
    # Registering redirects to the login page.
    response = await create_test_client.post(
        "/register", form={"username": "alice", "password": "secret123"}
    )
    assert response.status_code == 302

    # The new user can now log in and lands on the home feed.
    response = await create_test_client.post(
        "/login", form={"username": "alice", "password": "secret123"}
    )
    assert response.status_code == 302
    assert "/" in response.headers["Location"]
```

We post to register and assert we get a redirect, our sign that registration succeeded and sent us to login. Then we log in with the same credentials and check we're redirected again, this time toward the home feed. Because the test client keeps cookies between requests, the session set at login carries into later requests, which is exactly how we test logged-in behavior.

[Save the file](https://fmze.co/fftq-5.12.2).

The most valuable test is the one that proves fan-out works, because that logic is invisible in the interface. Create `tests/test_feed.py`:

{lang=python,line-numbers=on}
```
import pytest
from quart import current_app
from sqlalchemy import select

from post.models import feed_table


@pytest.mark.asyncio
async def test_post_fans_out_to_followers(create_test_client, create_test_app):
    # Two users: bob follows alice.
    await create_test_client.post("/register", form={"username": "alice", "password": "pw123456"})
    await create_test_client.post("/register", form={"username": "bob", "password": "pw123456"})

    await create_test_client.post("/login", form={"username": "bob", "password": "pw123456"})
    await create_test_client.post("/follow/alice")

    # alice posts.
    await create_test_client.post("/login", form={"username": "alice", "password": "pw123456"})
    await create_test_client.post("/post", form={"message": "hello world"})

    # The post should have landed in both alice's and bob's feeds.
    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            rows = (await conn.execute(select(feed_table))).fetchall()
            owners = {row.user_id for row in rows}
    assert len(owners) == 2
```

This test tells a little story: bob follows alice, alice posts, and we then look directly in the `feed` table. We assert there are feed rows for two distinct owners, alice and bob, proving the post fanned out to the follower and to the author. Checking the database directly like this is how we test side effects that never appear on a page.

[Save the file](https://fmze.co/fftq-5.12.3).

We should also make sure the live stream even connects. A full SSE test is involved because the stream never ends, but we can at least confirm the endpoint opens with the right content type. Add a quick check that a logged-in request to `/sse` returns an `text/event-stream` response, and that an anonymous one redirects to login, proving `login_required` guards it.

Run the whole suite inside the container, the same way we ran the counter tests:

{lang=bash,line-numbers=off}
```
$ docker compose up -d db
$ docker compose run --rm web uv run pytest
```

Green across the board. We've built QuartFeed from an empty boilerplate into a real social application: accounts, a follow graph, posts with images and permalinks, a materialized feed that fans out on write, live updates over Server Sent Events, comments that bubble, likes that collapse, and a test suite that guards it all. That's a genuinely production-shaped app, and you built every layer of it yourself.


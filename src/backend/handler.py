"""AWS Lambda entry points for the StudySpot backend.

Two handlers ship in one deployment package, so the API and the data it serves
can never be built from different revisions:

``handler.api``
    The Django application behind the CloudFront ``/api/*`` behavior. Mangum
    translates the Lambda function URL's event into the ASGI call Django
    expects.

``handler.manage``
    Runs a Django management command, invoked on demand. It exists because the
    database sits in a private subnet: ``manage.py migrate`` from a laptop
    cannot reach it, so migrations and data loads have to run inside the VPC.

The Vercel entry point is ``main.py`` beside this file. Both import the same
ASGI application; neither owns any behavior of its own.
"""

from __future__ import annotations

import json
import logging
import os
from io import StringIO
from typing import Any

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studyspot.settings")

import django  # noqa: E402
from mangum import Mangum  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402

from studyspot.asgi import application  # noqa: E402

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#: Only these may be invoked. A handler that ran whatever command the event
#: named would be a remote shell with the API's database credentials: the event
#: is data from the caller, not an instruction to be trusted.
ALLOWED_COMMANDS = {
    "migrate": {"no_input": True},
    "load_spots": {},
    "collectstatic": {"no_input": True},
    "showmigrations": {},
}

# lifespan="off": Django's ASGI application does not implement the lifespan
# protocol, and Mangum's "auto" would log a startup failure on every cold start.
api = Mangum(application, lifespan="off")


def manage(event: dict[str, Any] | None = None, context: Any = None) -> dict[str, Any]:
    """Run one allowed management command.

    .. code-block:: shell

        aws lambda invoke \\
          --function-name studyspot-staging-manage \\
          --payload '{"command": "migrate"}' \\
          --cli-binary-format raw-in-base64-out /dev/stdout

    Defaults to ``migrate`` so that an empty payload does the thing a fresh
    deployment always needs first.
    """
    command = (event or {}).get("command", "migrate")

    if command not in ALLOWED_COMMANDS:
        allowed = ", ".join(sorted(ALLOWED_COMMANDS))
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Unknown command {command!r}. Allowed: {allowed}."}),
        }

    output = StringIO()
    try:
        call_command(command, stdout=output, stderr=output, **ALLOWED_COMMANDS[command])
    except Exception as error:
        # Logged in full, returned in summary: a database error's text carries
        # the host and sometimes the failing statement.
        logger.exception("Management command %s failed", command)
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"command": command, "error": type(error).__name__, "output": output.getvalue()}
            ),
        }

    result = output.getvalue()
    logger.info("Management command %s finished: %s", command, result)
    return {"statusCode": 200, "body": json.dumps({"command": command, "output": result})}

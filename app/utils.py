import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import emails  # type: ignore
from jinja2 import Template
from jose import JWTError, jwt

from app.core.config import settings


@dataclass
class EmailData:
    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    """
    takes a template name and context dictionary as inputs and renders an HTML
    content using a template engine, returning the generated content as a string.

    Args:
        template_name (str): name of the email template to be rendered.
        context (dict[str, Any]): data to be inserted into the email template,
            allowing the `render` method of the `Template` class to replace
            placeholders with the actual content.

    Returns:
        str: an HTML content generated from a pre-defined email template based on
        the provided context.

    """
    template_str = (
        Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    """
    sends an email to a specified recipient using the provided subject and HTML
    content, utilizing the configured email settings from the application's
    configuration file.

    Args:
        email_to (str): recipient's email address to which the email message will
            be sent.
        subject (""): subject line of the email that will be sent.
        html_content (""): HTML content of the email that will be sent.

    """
    assert settings.emails_enabled, "no provided configuration for email variables"
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, smtp=smtp_options)
    logging.info(f"send email result: {response}")


def generate_test_email(email_to: str) -> EmailData:
    """
    creates an email message with a customized template and sends it to a provided
    email address.

    Args:
        email_to (str): recipient's email address for which the test email is to
            be generated.

    Returns:
        EmailData: an `EmailData` object containing the HTML content and subject
        line of a test email.

    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    """
    generates an email with a password recovery link for a user, using a templated
    email template and customizable context variables.

    Args:
        email_to (str): email address of the user to whom the password reset link
            will be sent.
        email (str): email address of the user to whom the password reset link
            will be sent.
        token (str): password reset token that is sent to the user's email address
            for password recovery.

    Returns:
        EmailData: an email data object containing the HTML content and subject
        of a password recovery email.

    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.server_host}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    """
    generates a new email for a user with their username, password, and an optional
    email address.

    Args:
        email_to (str): email address of the recipient to whom the new account
            details will be sent.
        username (str): username for the new account being generated.
        password (str): password for the new account to be generated.

    Returns:
        EmailData: an email data object containing the HTML content and subject
        line for a new account email.

    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.server_host,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_token(email: str) -> str:
    """
    generates a password reset token using a secret key and the current timestamp,
    expiration time, and the email address of the user.

    Args:
        email (str): email address of the user to whom the password reset token
            is being generated for, and it is used as the sub claim in the JWT
            token that is generated.

    Returns:
        str: a JSON Web Token (JWT) containing an expiration time and email address.

    """
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    """
    decodes a password reset token using a secret key and algorithm, and returns
    the sub claim of the decoded token if successful, or `None` otherwise.

    Args:
        token (str): password reset token to be verified.

    Returns:
        str | None: a string representing the subscriber ID of the user who reset
        their password.

    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"])
        return str(decoded_token["sub"])
    except JWTError:
        return None

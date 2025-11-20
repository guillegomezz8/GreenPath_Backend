from datetime import datetime
import secrets, string
import os, json, base64, logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apps.base.logger import configure_logging

from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string, TemplateDoesNotExist

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

configure_logging()

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def _gmail_creds_from_env():
    token_json = os.environ.get("GMAIL_TOKEN_JSON")
    client_secret_json = os.environ.get("GMAIL_CLIENT_SECRET_JSON")
    if not token_json or not client_secret_json:
        logging.error("Gmail API: faltan GMAIL_TOKEN_JSON o GMAIL_CLIENT_SECRET_JSON.")
        return None

    token_data = json.loads(token_json)
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes") or GMAIL_SCOPES,
    )
    if not creds.valid and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            logging.exception("Gmail API: error refrescando token: %s", e)
            return None
    return creds

def validate_files(request, field, update=False):
    """ 
    :params
    :request: request.data
    :field: key of file    
    """
    
    request = request.copy()

    if update:
        if type(request[field]) == str: request.__delitem__(field)
    else:
        if type(request[field]) == str: request.__setitem__(field, None)        

    return request

def format_date(date):
    date = datetime.strptime(date, '%d/%m/%Y')
    date = f"{date.year}-{date.month}-{date.day}"
    return date

def gen_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(12))

def send_access_email(user, temp_password, subject=None):
    try:
        to_email = user.email

        if not to_email:
            logging.error(f"send_access_email: el usuario {user} no tiene email.")
            return False
        if not subject:
            subject = "Acceso a GreenPath como Uusuario"
        context = {
            "username": user.username,
            "temp_password": temp_password,
            "year": timezone.now().year,
        }

        html = render_to_string("email/new_user.html", context)
        text = strip_tags(html)

        send_mail(
            subject,
            text,                              
            settings.EMAIL_HOST_USER,
            [to_email],
            html_message=html,
            fail_silently=False,
        )

        return True
    except Exception as e:
        logging.error(f"send_access_email: error enviando email a {getattr(user, 'email', None)}: {e}")
        return False

def send_access_email_google_api(user, temp_password, subject=None):
    try:
        to_email = getattr(user, "email", None)
        if not to_email:
            logging.error("send_access_email: el usuario %s no tiene email.", user)
            return False

        gmail_from = os.environ.get("GMAIL_FROM")
        if not gmail_from:
            logging.error("Gmail API: falta GMAIL_FROM.")
            return False

        subject = subject or "Acceso a GreenPath como Usuario"
        ctx = {
            "username": user.username,
            "temp_password": temp_password,
            "year": timezone.now().year,
        }

        html = render_to_string("email/new_user.html", ctx)
        text = strip_tags(html)

        msg = MIMEMultipart("alternative")
        msg["To"] = to_email
        msg["From"] = gmail_from
        msg["Subject"] = subject
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        creds = _gmail_creds_from_env()
        if not creds:
            return False

        service = build("gmail", "v1", credentials=creds)
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True

    except Exception as e:
        logging.exception("send_access_email (Gmail API): error enviando a %s: %s", getattr(user, "email", None), e)
        return False
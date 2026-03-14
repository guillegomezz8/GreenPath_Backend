from datetime import datetime
import base64
import json
import logging
import os
import secrets
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from celery import shared_task

from apps.base.literals import ACCESS_EMAIL_SUBJECT_USER
from apps.base.logger import configure_logging
from apps.user.models.user import User

from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

configure_logging()

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def _gmail_creds_from_env():
    try:
        token_json = os.environ.get("GMAIL_TOKEN_JSON")
        client_secret_json = os.environ.get("GMAIL_CLIENT_SECRET_JSON")
        if not token_json or not client_secret_json:
            logging.error("[base_utils - _gmail_creds_from_env] Gmail API: faltan GMAIL_TOKEN_JSON o GMAIL_CLIENT_SECRET_JSON.")
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
                logging.error(f"[base_utils - _gmail_creds_from_env] Gmail API: error refrescando token: {str(e)}")
                return None

        return creds
    except Exception as e:
        logging.error(f"[base_utils - _gmail_creds_from_env] Error construyendo credenciales Gmail: {str(e)}")
        return None


def send_email_google_api(to_email, subject, text_message, html_message=None):
    try:
        if not to_email:
            logging.error("[base_utils - send_email_google_api] Destinatario vacio.")
            return False

        gmail_from = os.environ.get("GMAIL_FROM")
        if not gmail_from:
            logging.error("[base_utils - send_email_google_api] Gmail API: falta GMAIL_FROM.")
            return False

        creds = _gmail_creds_from_env()
        if not creds:
            return False

        msg = MIMEMultipart("alternative")
        msg["To"] = to_email
        msg["From"] = gmail_from
        msg["Subject"] = subject or ACCESS_EMAIL_SUBJECT_USER
        msg.attach(MIMEText(text_message or "", "plain"))

        if html_message:
            msg.attach(MIMEText(html_message, "html"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        service = build("gmail", "v1", credentials=creds)
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except Exception as e:
        logging.error(f"[base_utils - send_email_google_api] Error enviando email por Gmail API a {to_email}: {str(e)}")
        return False


def validate_files(request, field, update=False):
    """
    :params
    :request: request.data
    :field: key of file
    """
    try:
        request = request.copy()

        if update:
            if type(request[field]) == str:
                request.__delitem__(field)
        else:
            if type(request[field]) == str:
                request.__setitem__(field, None)

        return request
    except Exception as e:
        logging.error(f"[base_utils - validate_files] Error validando ficheros del campo {field}: {str(e)}")
        raise


def format_date(date):
    try:
        date = datetime.strptime(date, '%d/%m/%Y')
        date = f"{date.year}-{date.month}-{date.day}"
        return date
    except Exception as e:
        logging.error(f"[base_utils - format_date] Error formateando fecha {date}: {str(e)}")
        raise


def gen_password():
    try:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(12))
    except Exception as e:
        logging.error(f"[base_utils - gen_password] Error generando password temporal: {str(e)}")
        raise


def send_access_email(user, temp_password, subject=None):
    try:
        to_email = user.email if user else None

        if not to_email:
            logging.error(f"[base_utils - send_access_email] El usuario {user} no tiene email.")
            return False
        if not subject:
            subject = ACCESS_EMAIL_SUBJECT_USER
        context = {
            "username": user.username,
            "temp_password": temp_password,
            "year": timezone.now().year,
        }

        html = render_to_string("email/new_user.html", context)
        text = strip_tags(html)

        return send_email_google_api(
            to_email=to_email,
            subject=subject,
            text_message=text,
            html_message=html,
        )
    except Exception as e:
        email_for_log = user.email if user else None
        logging.error(f"[base_utils - send_access_email] Error enviando email a {email_for_log}: {str(e)}")
        return False

@shared_task
def send_access_email_google_api(user_id, temp_password, subject=None):
    try:
        user = User.objects.filter(id=user_id).first()
        if not user:
            logging.error(f"[base_utils - send_access_email_google_api] Usuario no encontrado para envio de acceso: {user_id}")
            return False

        to_email = user.email if user else None
        if not to_email:
            logging.error(f"[base_utils - send_access_email_google_api] El usuario {user} no tiene email.")
            return False

        subject = subject or ACCESS_EMAIL_SUBJECT_USER
        ctx = {
            "username": user.username,
            "temp_password": temp_password,
            "year": timezone.now().year,
        }

        html = render_to_string("email/new_user.html", ctx)
        text = strip_tags(html)

        return send_email_google_api(
            to_email=to_email,
            subject=subject,
            text_message=text,
            html_message=html,
        )

    except Exception as e:
        email_for_log = None
        if user_id:
            user_for_log = User.objects.filter(id=user_id).first()
            if user_for_log:
                email_for_log = user_for_log.email
        logging.error(f"[base_utils - send_access_email_google_api] Error enviando email por Gmail API a {email_for_log}: {str(e)}")
        return False

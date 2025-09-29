from datetime import datetime
import logging, requests
import secrets, string

from apps.base.logger import configure_logging

from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.template import TemplateDoesNotExist

configure_logging()

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

def send_access_email_production(user, temp_password, subject=None):
    try:
        to_email = getattr(user, "email", None)
        if not to_email:
            logging.warning("send_access_email: usuario sin email: %s", user)
            return False

        if not settings.RESEND_API_KEY:
            logging.warning("send_access_email: falta RESEND_API_KEY, no se envía.")
            return False 

        subject = subject or "Acceso a GreenPath como Trabajador"
        ctx = {"username": user.username, "temp_password": temp_password, "year": timezone.now().year}

        try:
            html = render_to_string("email/new_user.html", ctx)
        except TemplateDoesNotExist:
            html = (
                f"<p>Hola {user.username},</p>"
                f"<p>Tu contraseña temporal es: <b>{temp_password}</b></p>"
                "<p>Por favor, cámbiala al iniciar sesión.</p>"
            )
        text = strip_tags(html)

        r = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.EMAIL_HOST_USER,
                "to": [to_email],
                "subject": subject,
                "html": html,
                "text": text,
            },
            timeout=10,
        )
        if not r.ok:
            logging.error("send_access_email: fallo API %s %s %s", r.status_code, r.text, r.headers)
        return r.ok
    except Exception as e:
        logging.exception("send_access_email: error: %s", e)
        return False
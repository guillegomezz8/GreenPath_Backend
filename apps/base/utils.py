from datetime import datetime
import logging
import secrets, string
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.mail import send_mail
from apps.base.logger import configure_logging

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
        logging.info(f"[send_access_email] INICIO - Usuario: {user.username}, ID: {user.id}")
        
        to_email = user.email
        logging.info(f"[send_access_email] Email destino: {to_email}")

        if not to_email:
            logging.error(f"[send_access_email] El usuario {user.username} no tiene email")
            return False
            
        if not subject:
            subject = "Acceso a GreenPath como Usuario"
        
        logging.info(f"[send_access_email] Subject: {subject}")
        logging.info(f"[send_access_email] Preparando contexto del template")
        
        context = {
            "username": user.username,
            "temp_password": temp_password,
            "year": timezone.now().year,
        }

        logging.info(f"[send_access_email] Renderizando template 'email/new_user.html'")
        html = render_to_string("email/new_user.html", context)
        text = strip_tags(html)
        logging.info(f"[send_access_email] Template renderizado correctamente. Longitud HTML: {len(html)}")

        logging.info(f"[send_access_email] Configuración SMTP:")
        logging.info(f"[send_access_email]   - HOST: {settings.EMAIL_HOST}")
        logging.info(f"[send_access_email]   - PORT: {settings.EMAIL_PORT}")
        logging.info(f"[send_access_email]   - USER: {settings.EMAIL_HOST_USER}")
        logging.info(f"[send_access_email]   - USE_TLS: {settings.EMAIL_USE_TLS}")
        logging.info(f"[send_access_email]   - USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', False)}")
        logging.info(f"[send_access_email]   - BACKEND: {settings.EMAIL_BACKEND}")
        
        logging.info(f"[send_access_email] Enviando email desde '{settings.EMAIL_HOST_USER}' a '{to_email}'")
        
        send_mail(
            subject,
            text,                              
            settings.EMAIL_HOST_USER,
            [to_email],
            html_message=html,
            fail_silently=False,
        )

        logging.info(f"[send_access_email] ✓ Email enviado EXITOSAMENTE a {to_email}")
        return True
        
    except Exception as e:
        logging.error(f"[send_access_email] ✗ ERROR enviando email a {getattr(user, 'email', 'N/A')}")
        logging.error(f"[send_access_email] Tipo de error: {type(e).__name__}")
        logging.error(f"[send_access_email] Mensaje: {str(e)}", exc_info=True)
        return False

from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import BadHeaderError
from django.core.exceptions import SuspiciousOperation

def send_hr_email(subject, message, recipient_list):
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            recipient_list,
            fail_silently=False,
        )
    except BadHeaderError:
        raise SuspiciousOperation("Invalid header found.")
    except Exception as e:
        # Handle other potential errors
        print(f"Error sending email: {e}")

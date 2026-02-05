import os
import time
import math
import logging
import pandas as pd
from typing import Dict, List
from dotenv import load_dotenv
from email.utils import make_msgid

from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.core.mail import get_connection

from .serializers import EmailTemplateSerializer

load_dotenv()
# -------------------
# Config
# -------------------

EMAIL_BATCH_LIMIT = 500          # Safe batch size (adjust if needed)
MAX_RETRIES = 3
RETRY_BACKOFF = 2              # exponential multiplier (2s, 4s, 8s)
REQUEST_TIMEOUT = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# -------------------
# Helpers
# -------------------

def chunk_list(items: List, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def build_recipients(user_info_df: pd.DataFrame, merge_info: Dict) -> List[Dict]:
    """
    Builds SMTP recipient payload safely.
    """
    recipients = []

    for _, row in user_info_df.iterrows():
        email = str(row.get("email", "")).strip()
        fullname = str(row.get("fullname", "")).strip()
        username = str(row.get("username", "")).strip()
        
        name = fullname if fullname else username 
        recipient_info = {
            **merge_info,
            "email": email,
            "name": name
        }
        
        email_serializer = EmailTemplateSerializer(data=recipient_info)
        if not email_serializer.is_valid(raise_exception=False):
            raise ValueError(f"Invalid recipient data: {email_serializer.errors}")
        
        recipients.append(email_serializer.validated_data)

    if not recipients:
        raise ValueError("No valid recipients found.")
    
    return recipients


def send_with_retry(recipients, connection=None):
    """
    Sends request with retry and exponential backoff.
    """
    for recipient in recipients:
        success = False
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                send_template_email(recipient, connection)
                success = True
                break
                
            except Exception as e:
                logging.error("Email error:", str(e))
                logging.error(f"Attempt {attempt} request error: {e}")

                if attempt < MAX_RETRIES:
                    sleep_time = RETRY_BACKOFF ** attempt
                    logging.info(f"Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                    
        if not success:
            raise RuntimeError(f"Max retries exceeded for {recipient['email']}")


# -------------------
# Main Sender
# -------------------

def send_template_email(context: Dict, connection=None):
    html = render_to_string("emails/welcome_update.html", context)
    text = strip_tags(html)
    
    
    msg = EmailMultiAlternatives(
        subject=f"Welcome back to {context['product_name']} 🚀",
        body=text,
        from_email="acctbank@acctboosterlinks.com",
        to=[context["email"]],
        connection=connection
    )
    msg.extra_headers = {
        "Reply-To": "acctbank@acctboosterlinks.com",
        "Message-ID": make_msgid(domain="acctboosterlinks.com"),
        # "Precedence": "bulk"
    }
    msg.attach_alternative(html, "text/html")

    sent = msg.send(fail_silently=False)

    if sent == 0:
        raise RuntimeError(f"SMTP rejected email to {context['email']}")
    

def send_single_message(merge_info: Dict):
    connection = get_connection()
    with connection:
        second_test_email = merge_info.copy()
        second_test_email["email"] = "samuelemeh200@gmail.com"
        send_with_retry(recipients=[merge_info, second_test_email], connection=connection)
    

def send_batch_message(
    merge_info: Dict,
):
    """
    Sends CSV users in batches to ZeptoMail safely.
    """
    connection = get_connection()
    is_test_mail = os.getenv("IS_TEST_MAIL", "false").lower() == "true"
    user_info_df = pd.read_csv("app/test_users.csv" if is_test_mail else "app/users.csv")
    recipients = build_recipients(user_info_df, merge_info)
    total = len(recipients)
    total_batches = math.ceil(total / EMAIL_BATCH_LIMIT)

    logging.info(f"Total recipients: {total}")
    logging.info(f"Sending in {total_batches} batches...")

    success_count = 0
    failed_batches = []

    with connection:
        for batch_index, batch in enumerate(chunk_list(recipients, EMAIL_BATCH_LIMIT), start=1):

            try:
                send_with_retry(batch, connection)
                logging.info(f"Batch {batch_index} sent successfully.")
                success_count += len(batch)

            except Exception as e:
                logging.error(f"Batch {batch_index} failed permanently: {e}")
                failed_batches.append(batch_index)

    logging.info("======================================")
    logging.info(f"Completed sending.")
    logging.info(f"Successful emails: {success_count}/{total}")
    logging.info(f"Failed batches: {failed_batches or 'None'}")

    return {
        "total": total,
        "sent": success_count,
        "failed_batches": failed_batches
    }

import os
import re
import json
import time
import math
import logging
import requests
import pandas as pd
from typing import Dict, List
from dotenv import load_dotenv


load_dotenv()
# -------------------
# Config
# -------------------

ZEPTO_BATCH_LIMIT = 500          # Safe batch size (adjust if needed)
MAX_RETRIES = 3
RETRY_BACKOFF = 2              # exponential multiplier (2s, 4s, 8s)
REQUEST_TIMEOUT = 30

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# -------------------
# Helpers
# -------------------

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))


def chunk_list(items: List, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def build_recipients(user_info_df: pd.DataFrame, merge_info: Dict) -> List[Dict]:
    """
    Builds ZeptoMail recipient payload safely.
    """
    recipients = []

    for _, row in user_info_df.iterrows():
        email = str(row.get("email", "")).strip()
        fullname = str(row.get("fullname", "")).strip()
        username = str(row.get("username", "")).strip()

        if not email or email.lower() == "nan":
            logging.warning("Skipping row: missing email")
            continue

        if not is_valid_email(email):
            logging.warning(f"Skipping invalid email: {email}")
            continue

        name = fullname if fullname and fullname.lower() != "nan" else username
        if not name or name.lower() == "nan":
            name = "User"

        recipients.append({
            "email_address": {
                "address": email,
                "name": name,
            },
            "merge_info": {
                **merge_info,
                "name": name
            }
        })

    if not recipients:
        raise ValueError("No valid recipients found.")

    return recipients


def send_with_retry(url, payload, headers):
    """
    Sends request with retry and exponential backoff.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code in (200, 201, 202):
                return response

            logging.error(
                f"Attempt {attempt} failed: {response.status_code} | {response.text}"
            )

        except requests.RequestException as e:
            logging.error(f"Attempt {attempt} request error: {e}")

        if attempt < MAX_RETRIES:
            sleep_time = RETRY_BACKOFF ** attempt
            logging.info(f"Retrying in {sleep_time}s...")
            time.sleep(sleep_time)

    raise RuntimeError("Max retries exceeded.")


# -------------------
# Main Sender
# -------------------

def send_single_message(email: str, merge_info: Dict):
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        raise EnvironmentError("API_KEY not set in environment.")

    url = "https://api.zeptomail.com/v1.1/email/template"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Zoho-enczapikey {API_KEY}",
    }
    
    payload = {
        "template_key": "2d6f.3d33dc3324b77a9d.k1.57f5bf90-f8a9-11f0-b303-765e7256bde4.19becef5209",
        "from": {
            "address": "acctbank@acctboosterlinks.com",
            "name": merge_info["team"]
        },
        "to": [
            {
                "email_address": {
                    "address": email,
                    "name": email.split("@")[0]
                }
            }
        ],
        "merge_info": merge_info
    }
    
    send_with_retry(url, payload, headers)
    

def send_batch_message(
    merge_info: Dict,
):
    """
    Sends CSV users in batches to ZeptoMail safely.
    """

    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        raise EnvironmentError("API_KEY not set in environment.")

    url = "https://api.zeptomail.com/v1.1/email/template/batch"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Zoho-enczapikey {API_KEY}",
    }

    # user_info_df = pd.read_csv("users.csv")
    user_info_df = pd.read_csv("app/test_users.csv")
    recipients = build_recipients(user_info_df, merge_info)
    total = len(recipients)
    total_batches = math.ceil(total / ZEPTO_BATCH_LIMIT)

    logging.info(f"Total recipients: {total}")
    logging.info(f"Sending in {total_batches} batches...")

    success_count = 0
    failed_batches = []

    for batch_index, batch in enumerate(chunk_list(recipients, ZEPTO_BATCH_LIMIT), start=1):
        logging.info(f"Sending batch {batch_index}/{total_batches} ({len(batch)} emails)")

        payload = {
            "template_key": "2d6f.3d33dc3324b77a9d.k1.57f5bf90-f8a9-11f0-b303-765e7256bde4.19becef5209",
            "from": {
                "address": "acctbank@acctboosterlinks.com",
                "name": merge_info["team"]
            },
            "to": batch
        }

        try:
            send_with_retry(url, payload, headers)
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

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import PyJWTError
from sqlalchemy.orm import Session
import os
import logging

from .database import get_db
from . import models

import bcrypt

logger = logging.getLogger(__name__)

# Environment config secret — persistent default fallback for local dev/hot-reloads
SECRET_KEY = os.getenv("SECRET_KEY") or "mentor_me_secure_jwt_secret_key_persistent_2026"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    import time
    to_encode = data.copy()
    seconds = expires_delta.total_seconds() if expires_delta else ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expire_epoch = int(time.time() + seconds)
    to_encode.update({"exp": expire_epoch})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception as e:
        logger.debug("Token verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.debug("JWT validation failed: 'sub' claim is missing")
            raise credentials_exception
    except PyJWTError as e:
        logger.debug("JWT validation failed: %s", e)
        raise credentials_exception
        
    user = db.query(models.User).filter((models.User.id == user_id) | (models.User.email == user_id)).first()
    if user is None:
        logger.debug("JWT validation failed: user not found in database")
        raise credentials_exception
    return user

def require_role(allowed_roles: list[str]):
    def role_dependency(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return current_user
    return role_dependency

def generate_otp_code(length: int = 6) -> str:
    import secrets
    return "".join(secrets.choice("0123456789") for _ in range(length))

def create_2fa_challenge_token(user_id: str, otp_code: str, email: str, role: str, expires_minutes: int = 5) -> str:
    import time
    import hashlib
    otp_hash = hashlib.sha256(f"{otp_code}:{SECRET_KEY}".encode('utf-8')).hexdigest()
    payload = {
        "purpose": "2fa_challenge",
        "sub": user_id,
        "email": email,
        "role": role,
        "otp_hash": otp_hash,
        "exp": int(time.time() + (expires_minutes * 60))
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_2fa_challenge_token(challenge_token: str, submitted_code: str) -> dict:
    import hashlib
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Security challenge code is invalid or has expired. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(challenge_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "2fa_challenge":
            raise credentials_exception
            
        expected_hash = payload.get("otp_hash")
        calc_hash = hashlib.sha256(f"{submitted_code.strip()}:{SECRET_KEY}".encode('utf-8')).hexdigest()
        
        if expected_hash != calc_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect 6-digit security code. Please check and try again."
            )
        return payload
    except PyJWTError:
        raise credentials_exception


def create_password_reset_challenge_token(user_id: str, otp_code: str, email: str, expires_minutes: int = 15) -> str:
    import time
    import hashlib
    otp_hash = hashlib.sha256(f"{otp_code}:{SECRET_KEY}".encode('utf-8')).hexdigest()
    payload = {
        "purpose": "password_reset",
        "sub": user_id,
        "email": email,
        "otp_hash": otp_hash,
        "exp": int(time.time() + (expires_minutes * 60))
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_challenge_token(challenge_token: str, submitted_code: str) -> dict:
    import hashlib
    credentials_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password reset session is invalid or has expired. Please request a new code.",
    )
    try:
        payload = jwt.decode(challenge_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise credentials_exception
            
        expected_hash = payload.get("otp_hash")
        calc_hash = hashlib.sha256(f"{submitted_code.strip()}:{SECRET_KEY}".encode('utf-8')).hexdigest()
        
        if expected_hash != calc_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect 6-digit password reset code. Please check and try again."
            )
        return payload
    except PyJWTError:
        raise credentials_exception


def send_email_via_resend(to_email: str, subject: str, body_text: str, body_html: str = None) -> bool:
    """
    Sends an email using the Resend REST API (HTTPS on port 443).
    Bypasses SMTP port blocking on cloud hosts like Railway.
    """
    raw_key = os.getenv("RESEND_API_KEY")
    if not raw_key:
        return False
    resend_api_key = raw_key.strip(' "\'')
    if not resend_api_key:
        return False

    raw_from = os.getenv("RESEND_FROM_EMAIL") or os.getenv("SMTP_FROM_EMAIL")
    custom_from = raw_from.strip(' "\'') if raw_from else None

    # Resend requires a verified domain for custom senders.
    # Public domains (@gmail.com, @yahoo.com) cannot be verified, so we use onboarding@resend.dev.
    from_candidates = []
    if custom_from:
        lower_from = custom_from.lower()
        if any(dom in lower_from for dom in ["@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com", "@icloud.com"]):
            from_candidates.append("Mentoring-Me <onboarding@resend.dev>")
        else:
            from_candidates.append(f"Mentoring-Me <{custom_from}>" if "<" not in custom_from else custom_from)
            from_candidates.append("Mentoring-Me <onboarding@resend.dev>")
    else:
        from_candidates.append("Mentoring-Me <onboarding@resend.dev>")

    html_content = body_html or f"<div style='font-family: Arial, sans-serif; font-size: 15px; color: #333; line-height: 1.6;'>{body_text.replace(chr(10), '<br>')}</div>"

    headers = {
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json"
    }

    import requests
    for from_addr in from_candidates:
        payload = {
            "from": from_addr,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
            "text": body_text
        }
        try:
            try:
                res = requests.post("https://api.resend.com/emails", headers=headers, json=payload, timeout=10)
            except requests.exceptions.SSLError:
                res = requests.post("https://api.resend.com/emails", headers=headers, json=payload, verify=False, timeout=10)

            if res.status_code in (200, 201):
                print(f"[RESEND SUCCESS] Verification email successfully sent to {to_email} via Resend (from: {from_addr})")
                return True
            else:
                print(f"[RESEND NOTICE] Attempt with {from_addr} returned {res.status_code}: {res.text}")
        except Exception as e:
            print(f"[RESEND ERROR] Failed to send via Resend using {from_addr}: {e}")

    return False


def send_email_notification(to_email: str, subject: str, body_text: str, body_html: str = None, reply_to: str = None) -> bool:
    """
    Sends an email via Resend API (HTTPS) or SMTP fallback.
    Automatically cleans quotes and whitespace from environment variables.
    """
    # 1. Try Resend API (HTTPS Port 443) first - Works everywhere including Railway
    if os.getenv("RESEND_API_KEY"):
        if send_email_via_resend(to_email, subject, body_text, body_html):
            return True
        print("[EMAIL DISPATCH] Resend failed or was rejected, attempting SMTP fallback...")

    # 2. Fallback to SMTP
    raw_host = os.getenv("SMTP_HOST")
    smtp_host = raw_host.strip(' "\'') if raw_host else None

    raw_port = os.getenv("SMTP_PORT", "587")
    try:
        smtp_port = int(str(raw_port).strip(' "\''))
    except Exception:
        smtp_port = 587

    raw_user = os.getenv("SMTP_USER")
    smtp_user = raw_user.strip(' "\'') if raw_user else None

    raw_pass = os.getenv("SMTP_PASSWORD")
    smtp_password = raw_pass.strip(' "\'') if raw_pass else None

    raw_from = os.getenv("SMTP_FROM_EMAIL")
    smtp_from = raw_from.strip(' "\'') if raw_from else (smtp_user or "support@mentoring-me.app")

    if smtp_host and smtp_user and smtp_password:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_from
            msg["To"] = to_email
            if reply_to:
                msg["Reply-To"] = reply_to

            part1 = MIMEText(body_text, "plain")
            msg.attach(part1)
            if body_html:
                part2 = MIMEText(body_html, "html")
                msg.attach(part2)

            sent = False
            # Try Port 465 (Direct SSL) first - most reliable on cloud containers
            try:
                with smtplib.SMTP_SSL(smtp_host, 465, timeout=10) as server_ssl:
                    server_ssl.login(smtp_user, smtp_password)
                    server_ssl.sendmail(smtp_from, to_email, msg.as_string())
                sent = True
                print(f"[SMTP SUCCESS - SSL 465] Verification email successfully sent to {to_email}")
                return True
            except Exception as e_ssl:
                print(f"[SMTP SSL 465 Notice]: {e_ssl}")

            # Fallback to Port 587 (STARTTLS)
            if not sent:
                try:
                    with smtplib.SMTP(smtp_host, 587, timeout=10) as server_tls:
                        server_tls.starttls()
                        server_tls.login(smtp_user, smtp_password)
                        server_tls.sendmail(smtp_from, to_email, msg.as_string())
                    sent = True
                    print(f"[SMTP SUCCESS - TLS 587] Verification email successfully sent to {to_email}")
                    return True
                except Exception as e_tls:
                    print(f"[SMTP TLS 587 Notice]: {e_tls}")

            return False
        except Exception as e:
            print(f"[SMTP ERROR] Failed to send email to {to_email}: {e}")
            return False
    else:
        print(f"[SMTP NOTICE] Missing credentials: host={bool(smtp_host)}, user={bool(smtp_user)}, pass={bool(smtp_password)}")
        return False



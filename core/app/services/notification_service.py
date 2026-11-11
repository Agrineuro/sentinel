import base64
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from sqlalchemy.orm import Session
from app.models.alert import AlertModel
from app.models.notification import NotificationDestinationModel, NotificationDeliveryModel
from app.vault.service import vault_service


def _body(alert: AlertModel) -> str:
    return "\n".join([
        f"Sentinel alert: {alert.title}",
        f"Severity: {alert.severity}",
        f"System: {alert.entity or 'Unknown'}",
        "",
        alert.summary,
        "",
        f"Alert ID: {alert.id}",
        f"Triggered: {alert.triggered_at.isoformat()}",
    ])


def send(destination: NotificationDestinationModel, recipient: str, secret: str, message: str, *, test=False) -> None:
    config = destination.config or {}
    if destination.channel_type == "email":
        email = EmailMessage()
        email["From"] = config["from_address"]
        email["To"] = recipient
        email["Subject"] = "[Sentinel] Test notification" if test else "[Sentinel] " + message.splitlines()[0].replace("Sentinel alert: ", "")
        email.set_content(message)
        host = config["smtp_host"]
        port = int(config.get("smtp_port", 587))
        context = ssl.create_default_context()
        if config.get("security", "starttls") == "ssl":
            client = smtplib.SMTP_SSL(host, port, timeout=10, context=context)
        else:
            client = smtplib.SMTP(host, port, timeout=10)
        with client:
            if config.get("security", "starttls") == "starttls":
                client.starttls(context=context)
                client.ehlo()
            username = str(config.get("smtp_username") or "")
            if username:
                client.login(username, secret)
            client.send_message(email)
        return
    sid = config["account_sid"]
    url = "https://api.twilio.com/2010-04-01/Accounts/" + sid + "/Messages.json"
    body = "Sentinel test notification: delivery is working." if test else message
    data = urlencode({"To": recipient, "From": config["from_number"], "Body": body[:1500]}).encode()
    auth = base64.b64encode((sid + ":" + secret).encode()).decode()
    request = Request(url, data=data, headers={"Authorization": "Basic " + auth, "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urlopen(request, timeout=12) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError("SMS provider rejected the message")


def _mask(channel_type: str, recipient: str) -> str:
    if channel_type == "sms":
        return "***" + recipient[-4:]
    local, _, domain = recipient.partition("@")
    return (local[:1] + "***@" + domain) if domain else "***"


def destination_read(row: NotificationDestinationModel, db: Session) -> dict:
    credential = vault_service.get(db, row.credential_id)
    return {
        "id": row.id, "name": row.name, "channel_type": row.channel_type,
        "masked_destination": _mask(row.channel_type, credential.username if credential else ""),
        "enabled": row.enabled, "status": row.status,
        "last_error": row.last_error, "created_at": row.created_at,
    }


def create_destination(db: Session, payload, owner_user_id: str):
    from uuid import uuid4
    from app.schemas.vault import CredentialCreate
    credential = vault_service.create_credential(db, CredentialCreate(
        name=payload.name + " notification destination",
        username=payload.destination.strip(),
        password=payload.provider_secret,
        credential_type="notification_" + payload.channel_type,
    ))
    row = NotificationDestinationModel(
        id="notify_" + uuid4().hex, name=payload.name.strip(),
        channel_type=payload.channel_type, config=payload.config,
        credential_id=credential.id, owner_user_id=owner_user_id,
        enabled=True, status="unverified",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_destination(db: Session, row: NotificationDestinationModel) -> None:
    credential = vault_service.get(db, row.credential_id)
    if not credential or credential.credential_type != "notification_" + row.channel_type:
        raise RuntimeError("Notification destination credential is unavailable")
    send(row, credential.username, credential.secret, "Sentinel test notification: delivery is working.", test=True)
    row.status = "verified"
    row.last_error = None
    db.commit()


def process_pending(db: Session, limit: int = 25) -> int:
    now = datetime.now(timezone.utc)
    deliveries = (db.query(NotificationDeliveryModel)
                  .join(NotificationDestinationModel, NotificationDestinationModel.id == NotificationDeliveryModel.destination_id)
                  .filter(NotificationDeliveryModel.status == "pending",
                          NotificationDeliveryModel.next_attempt_at <= now,
                          NotificationDestinationModel.enabled.is_(True))
                  .order_by(NotificationDeliveryModel.next_attempt_at.asc())
                  .limit(limit).all())
    sent = 0
    for delivery in deliveries:
        alert = db.query(AlertModel).filter(AlertModel.id == delivery.alert_id).first()
        destination = db.query(NotificationDestinationModel).filter(
            NotificationDestinationModel.id == delivery.destination_id).first()
        credential = vault_service.get(db, destination.credential_id) if destination and destination.enabled else None
        try:
            if alert is None or destination is None or credential is None:
                raise RuntimeError("Alert, enabled destination, or encrypted destination credential is missing")
            if credential.credential_type != "notification_" + destination.channel_type:
                raise RuntimeError("Notification destination credential type does not match")
            send(destination, credential.username, credential.secret, _body(alert))
            delivery.status = "sent"
            delivery.sent_at = now
            delivery.last_error = None
            destination.status = "verified"
            destination.last_error = None
            sent += 1
        except Exception as exc:
            delivery.attempts += 1
            delivery.last_error = type(exc).__name__
            if destination:
                destination.last_error = type(exc).__name__
                destination.status = "error"
            if delivery.attempts >= 5:
                delivery.status = "failed"
            else:
                delivery.next_attempt_at = now + timedelta(seconds=min(3600, 30 * (2 ** delivery.attempts)))
        db.commit()
    return sent

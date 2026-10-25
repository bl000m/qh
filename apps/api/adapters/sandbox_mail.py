"""SMTP delivery only to an explicitly local, non-relaying development mailbox."""
import asyncio
from email.message import EmailMessage
import smtplib

from app.projections.guest import MailUnavailable


class SandboxSMTPMailer:
    def __init__(self, *, host='qh-guest-mailbox', port=1025):
        if host not in ('qh-guest-mailbox', 'localhost', '127.0.0.1') or not 1 <= port <= 65535:
            raise ValueError('Local sandbox SMTP target required')
        self.host, self.port = host, port

    def _send(self, delivery, code):
        try:
            message = EmailMessage()
            message['From'] = 'no-reply@qh.example.test'
            message['To'] = delivery.recipient
            message['Subject'] = 'Votre code QH'
            message.set_content('Code de vérification QH : '+code+'\nExpiration : '+delivery.expires_at.isoformat()
                +'\nCe code prouve le contrôle de cette boîte email, pas une identité civile. '
                'Si vous n’avez pas demandé cet accès, ignorez ce message.')
            with smtplib.SMTP(self.host, self.port, timeout=3) as smtp:
                smtp.send_message(message)
        except Exception:
            raise MailUnavailable('Sandbox mail unavailable') from None

    async def send(self, delivery, code):
        await asyncio.to_thread(self._send, delivery, code)

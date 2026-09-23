"""Transport contracts and deterministic offline fakes.

Adapters accept already-connected clients; this package never connects to SMTP/IMAP.
Engine refuses these adapters for now (offline=False); live enablement is separate.
"""
from email import policy
from email.parser import Parser
import smtplib
import imaplib
from .engine import DefiniteFailure


class SMTPAdapter:
    offline=False
    def __init__(self, client: smtplib.SMTP):
        self.client=client
    def send(self,message_id,body):
        try:
            refused=self.client.send_message(Parser(policy=policy.default).parsestr(body))
            if refused:
                raise DefiniteFailure('Recipient refused')
        except (smtplib.SMTPRecipientsRefused,smtplib.SMTPSenderRefused,smtplib.SMTPDataError,smtplib.SMTPHeloError) as error:
            code=getattr(error,'smtp_code',None)
            if isinstance(error,smtplib.SMTPRecipientsRefused) or (isinstance(code,int) and 400<=code<600):
                raise DefiniteFailure('Explicit SMTP rejection') from error
            raise
        except ConnectionRefusedError as error:
            raise DefiniteFailure('Connection refused before DATA') from error


class IMAPAdapter:
    offline=False
    def __init__(self,client: imaplib.IMAP4_SSL,sent_folder):
        self.client,self.folder=client,sent_folder
    def contains(self,mailbox,message_id):
        if any(c in message_id for c in '\r\n"\\'):
            raise ValueError('Invalid Message-ID')
        status,_=self.client.select(self.folder,readonly=True)
        if status!='OK':
            raise OSError('Cannot read Sent folder')
        status,data=self.client.search(None,'HEADER','Message-ID','"'+message_id+'"')
        if status!='OK':
            raise OSError('IMAP search failed')
        return bool(data and data[0])


class FakeSMTP:
    offline=True
    def __init__(self,outcomes=(),sent_copy=True):
        self.outcomes=list(outcomes); self.accepted=[]; self.sent=set(); self.sent_copy=sent_copy
    def send(self,message_id,body):
        outcome=self.outcomes.pop(0) if self.outcomes else 'sent'
        if outcome=='failed':
            raise DefiniteFailure('Fake explicit rejection')
        if outcome=='timeout':
            raise TimeoutError('Fake unknown SMTP outcome')
        self.accepted.append((message_id,body))
        if self.sent_copy:
            self.sent.add(message_id)
        if outcome=='timeout_accepted':
            raise TimeoutError('Accepted, but final response lost')
        if outcome=='crash':
            raise KeyboardInterrupt('Simulated process loss after SMTP acceptance')


class FakeIMAP:
    offline=True
    def __init__(self,sent=(),available=True):
        self.sent=sent; self.available=available
    def contains(self,mailbox,message_id):
        if not self.available:
            raise OSError('Fake mailbox unavailable')
        return message_id in self.sent

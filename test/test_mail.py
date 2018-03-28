import email
import imaplib
import logging
import os
import pytest
import secrets
import string
import smtplib

from email.utils import COMMASPACE, formataddr
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

pytestmark = []

logging.basicConfig(level=logging.DEBUG)

SMTP_HOST = "smtp-sink"
SMTP_PORT = 25
IMAP_HOST = "courier-imap"
IMAP_PORT = 143
IMAP_USER = 'smtp'
IMAP_PASS = 'smtp'

ATTACHMENTS_DIR = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'attachments')


def get_random_email_address():

    alphabet1 = string.ascii_letters

    username = ''.join(secrets.choice(alphabet1) for i in range(8))
    hostname = ''.join(secrets.choice(alphabet1) for i in range(8))
    address = '{0}@{1}.com'.format(username,hostname)

    return address


def get_random_email_text(length=10,splits=0):

    alphabet1 = string.ascii_letters

    text = ''.join(secrets.choice(alphabet1) for i in range(length))

    for _ in range(splits):
        # no spaces at beginning or end of text
        i = secrets.choice(range(1,length-1))
        text = text[:i] + ' ' + text[i+1:]

    return text


def send_email(fromaddr: str, toaddrs: list, subject: str,
        body: str, attachments=[]):
    """helper function for sending emails

    fromaddr : string of sender email address
    toaddrs : list of recipient email addresses
    """

    # Create the message
    msg = MIMEMultipart()
    msg['To'] = COMMASPACE.join(toaddrs)
    msg['From'] = formataddr((None,fromaddr))
    msg['Subject'] = subject
    msg.attach(MIMEText(body))

    # Attach attachments
    for fname in attachments:
        with open(fname,'rb') as f:
            # create the attachment
            part = MIMEApplication(f.read(), Name=os.path.basename(fname))
        # save the attachment to the message
        part['Content-Disposition'] = \
            'attachment; filename="%s"' % os.path.basename(fname)
        msg.attach(part)


    # Send the message
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtpconn:
        smtpconn.sendmail(fromaddr, toaddrs, msg.as_string())

    return msg


def get_message_matchings(pattern):

    # list of messages matching pattern
    messages = []

    with imaplib.IMAP4(IMAP_HOST,IMAP_PORT) as M:

        # login to the imap server
        M.login(IMAP_USER, IMAP_PASS)

        # navigate to the INBOX
        M.select()

        # search for all messages matching the given pattern
        typ, msgnums = M.search(None,pattern)

        for msgnum in msgnums[0].split():

            # get the message data
            rv, data = M.fetch(msgnum,'(RFC822)')

            for response_part in data:
                if isinstance(response_part, tuple):
                    messages.append(email.message_from_bytes(response_part[1]))

    return messages


def compare_emails(sent_msg, recv_msg):
    """helper function for comparing messages"""

    # check that it is a multipart message
    assert sent_msg.is_multipart() == recv_msg.is_multipart()

    sent_msg_parts = sent_msg.get_payload()
    recv_msg_parts = recv_msg.get_payload()

    # should be two parts, body (text) and file data (application)
    assert len(sent_msg_parts) == len(recv_msg_parts)

    for i in range(len(sent_msg_parts)):

        sent_msg_part = sent_msg_parts[i].get_payload(decode=True)
        recv_msg_part = recv_msg_parts[i].get_payload(decode=True)

        # received body should match sent body
        assert recv_msg_part == sent_msg_part


class TestMail(object):

    def test_send_mail(self):
        """send email and fetch it from the server"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address()]
        subject = get_random_email_text(10)
        body = get_random_email_text(30,7)

        sent_msg = send_email(fromaddr, toaddrs, subject, body)

        # retrieve the message from the IMAP server
        pattern = '(TO "{}")'.format(toaddrs[0])
        messages = get_message_matchings(pattern)

        assert len(messages) == 1

        recv_msg = messages[0]

        # make sure the message we sent matches the message we received
        compare_emails(sent_msg, recv_msg)


    def test_send_mail_attachment_text(self):
        """semd email with a text file attachment"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address()]
        subject = get_random_email_text(10)
        body = get_random_email_text(30,7)

        attachments=[os.path.join(ATTACHMENTS_DIR,'hello.txt')]

        sent_msg = send_email(fromaddr, toaddrs, subject, body, attachments)

        # retrieve the message from the IMAP server
        pattern = '(TO "{}")'.format(toaddrs[0])
        messages = get_message_matchings(pattern)

        assert len(messages) == 1

        recv_msg = messages[0]

        # make sure the message we sent matches the message we received
        compare_emails(sent_msg, recv_msg)


    def test_send_mail_attachment_tgz(self):
        """send email with a tgz attachment"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address()]
        subject = get_random_email_text(10)
        body = get_random_email_text(30,7)

        attachments=[os.path.join(ATTACHMENTS_DIR,'hello.tgz')]

        sent_msg = send_email(fromaddr, toaddrs, subject, body, attachments)

        # retrieve the message from the IMAP server
        pattern = '(TO "{}")'.format(toaddrs[0])
        messages = get_message_matchings(pattern)

        assert len(messages) == 1

        recv_msg = messages[0]

        # make sure the message we sent matches the message we received
        compare_emails(sent_msg, recv_msg)


    def test_send_multiple_mails(self):
        """fetching multiple emails from the server"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address()]

        subject1 = get_random_email_text(10)
        body1 = get_random_email_text(30,7)
        sent_msg1 = send_email(fromaddr, toaddrs, subject1, body1)

        subject2 = get_random_email_text(10)
        body2 = get_random_email_text(30,7)
        sent_msg2 = send_email(fromaddr, toaddrs, subject2, body2)

        subject3 = get_random_email_text(10)
        body3 = get_random_email_text(30,7)
        sent_msg3 = send_email(fromaddr, toaddrs, subject3, body3)

        sent_msgs = [sent_msg1, sent_msg2, sent_msg3]

        # retrieve the messages from the IMAP server
        pattern = '(TO "{}")'.format(toaddrs[0])
        recv_msgs = get_message_matchings(pattern)

        assert len(recv_msgs) == 3

        # sort the messages by subject so we can try to compare
        # emails in the correct order
        sent_msgs.sort(key=lambda m: m['Subject'])
        recv_msgs.sort(key=lambda m: m['Subject'])

        for sent_msg,recv_msg in zip(sent_msgs,recv_msgs):
            # make sure the message we sent matches the message we received
            compare_emails(sent_msg, recv_msg)


    def test_message_filter_multiple_toaddrs_in_order(self):
        """filtering based on a multiple toaddrs"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address(),get_random_email_address()]
        subject = get_random_email_text(10)
        body = get_random_email_text(30,7)

        sent_msg = send_email(fromaddr, toaddrs, subject, body)

        # retrieve the message from the IMAP server
        pattern = '(TO "{}") (TO "{}")'.format(toaddrs[0],toaddrs[1])
        messages = get_message_matchings(pattern)

        assert len(messages) == 1

        recv_msg = messages[0]

        # make sure the message we sent matches the message we received
        compare_emails(sent_msg, recv_msg)


    def test_message_filter_multiple_toaddrs_partial_begin(self):
        """filtering based on partial toaddrs, match at beginning"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address(),get_random_email_address()]
        subject = get_random_email_text(10)
        body = get_random_email_text(30,7)

        sent_msg = send_email(fromaddr, toaddrs, subject, body)

        # retrieve the message from the IMAP server
        pattern = '(TO "{}")'.format(toaddrs[0])
        messages = get_message_matchings(pattern)

        assert len(messages) == 1

        recv_msg = messages[0]

        # make sure the message we sent matches the message we received
        compare_emails(sent_msg, recv_msg)


    def test_message_filter_multiple_toaddrs_partial_end(self):
        """filtering based on partial toaddrs, match at end"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address(),get_random_email_address()]
        subject = get_random_email_text(10)
        body = get_random_email_text(30,7)

        sent_msg = send_email(fromaddr, toaddrs, subject, body)

        # retrieve the message from the IMAP server
        pattern = '(TO "{}")'.format(toaddrs[1])
        messages = get_message_matchings(pattern)

        assert len(messages) == 1

        recv_msg = messages[0]

        # make sure the message we sent matches the message we received
        compare_emails(sent_msg, recv_msg)


    def test_message_filter_single_fromaddr(self):
        """filtering based on the fromaddr"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address()]
        subject = get_random_email_text(10)
        body = get_random_email_text(30,7)

        sent_msg = send_email(fromaddr, toaddrs, subject, body)

        # retrieve the message from the IMAP server
        pattern = '(FROM "{}")'.format(fromaddr)
        messages = get_message_matchings(pattern)

        assert len(messages) == 1

        recv_msg = messages[0]

        # make sure the message we sent matches the message we received
        compare_emails(sent_msg, recv_msg)


    def test_message_filter_subject_full(self):
        """filtering based on the full subject"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address()]
        subject = get_random_email_text(10)
        body = get_random_email_text(30,7)

        sent_msg = send_email(fromaddr, toaddrs, subject, body)

        # retrieve the message from the IMAP server
        pattern = '(SUBJECT "{}")'.format(subject)
        messages = get_message_matchings(pattern)

        assert len(messages) == 1

        recv_msg = messages[0]

        # make sure the message we sent matches the message we received
        compare_emails(sent_msg, recv_msg)


    def test_message_filter_subject_partial(self):
        """filtering based on part of the subject"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address()]
        subject = get_random_email_text(10)
        body = get_random_email_text(30,7)

        sent_msg = send_email(fromaddr, toaddrs, subject, body)

        # retrieve the message from the IMAP server
        pattern = '(SUBJECT "{}")'.format(subject[2:8])
        messages = get_message_matchings(pattern)

        assert len(messages) == 1

        recv_msg = messages[0]

        # make sure the message we sent matches the message we received
        compare_emails(sent_msg, recv_msg)


    def test_message_filter_body_full(self):
        """filtering based on the full body"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address()]
        subject = get_random_email_text(10)
        body = get_random_email_text(30,7)

        sent_msg = send_email(fromaddr, toaddrs, subject, body)

        # retrieve the message from the IMAP server
        pattern = '(BODY "{}")'.format(body)
        messages = get_message_matchings(pattern)

        assert len(messages) == 1

        recv_msg = messages[0]

        # make sure the message we sent matches the message we received
        compare_emails(sent_msg, recv_msg)


    def test_message_filter_body_partial(self):
        """filtering based on part of the body"""

        fromaddr = get_random_email_address()
        toaddrs = [get_random_email_address()]
        subject = get_random_email_text(10)
        body = get_random_email_text(30,7)

        sent_msg = send_email(fromaddr, toaddrs, subject, body)

        # retrieve the message from the IMAP server
        pattern = '(BODY "{}")'.format(body[7:20])
        messages = get_message_matchings(pattern)

        assert len(messages) == 1

        recv_msg = messages[0]

        # make sure the message we sent matches the message we received
        compare_emails(sent_msg, recv_msg)


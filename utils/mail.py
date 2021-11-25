import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import html2text
from jinja2 import Template

from config import EMAIL_HOST, EMAIL_PORT, EMAIL_TLS, EMAIL_RECIPIENTS, EMAIL_PASSWORD, EMAIL_LOGIN, EMAIL_FROM


def read_template(filename) -> Template:
    """
    Returns a Template object comprising the contents of the file specified by filename.
    """
    tmpl_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "templates", filename)

    with open(tmpl_file, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()

    return Template(template_file_content)


def send_email(subject: str, template: str, params: dict):
    """
    Send email taking necessary configuration from config.py

    :param subject: email subject
    :param template: template file to use
    :param params: substitute params dictionary
    """

    tmpl = read_template(template)

    with smtplib.SMTP(host=EMAIL_HOST, port=EMAIL_PORT) as smtp:
        if EMAIL_TLS:
            smtp.starttls()

        if EMAIL_LOGIN is not None:
            smtp.login(EMAIL_LOGIN, EMAIL_PASSWORD)

        # For each contact, send the email:
        for name, email in EMAIL_RECIPIENTS:
            msg = MIMEMultipart()

            msg['From'] = EMAIL_FROM
            msg['To'] = email
            msg['Subject'] = subject

            body = tmpl.render(params, PERSON_NAME=name.title())

            if template.endswith(".html"):
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(html2text.html2text(body), 'plain'))

            smtp.send_message(msg)
            del msg

        smtp.quit()

import logging
import os
from datetime import datetime
from email.mime.image import MIMEImage
from os.path import dirname, join

import django.core.mail
import pandas as pd
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from dotenv import load_dotenv
from sqlalchemy import create_engine

from ad_main import settings
from dados.episem import episem

env_file = os.environ.get('ENV_FILE', '.env')

dotenv_path = join(dirname(dirname(dirname(__file__))), env_file)
load_dotenv(dotenv_path)


PSQL_URI = "postgresql://{}:{}@{}:{}/{}".format(
    settings.PSQL_USER,
    settings.PSQL_PASSWORD,
    settings.PSQL_HOST,
    settings.PSQL_PORT,
    settings.PSQL_DBF,
)
db_engine = create_engine(PSQL_URI)

dt_now = datetime.now().strftime('%Y-%m-%d')
year_week = episem(dt_now, sep='')
year, week = year_week[:4], year_week[-2:]
last_week = int(week) - 1


def get_partner_active():
    """
    :param: name, contact, email
        where status is True
    :return: pandas dataframe
    """
    sql = '''
      SELECT name, contact, email FROM dbf_sendtoPartner
      WHERE status = 'True'
      ORDER BY name
    '''

    with db_engine.connect() as conn:
        return pd.read_sql(sql, conn)


class MissingConnectionException(Exception):
    pass


def get_connection(label=None, **kwargs):
    if label is None:
        label = getattr(settings, 'EMAIL_CONNECTION_DEFAULT', None)

    try:
        connections = getattr(settings, 'EMAIL_CONNECTIONS')
        options = connections[label]
    except KeyError:
        raise MissingConnectionException(
            'Settings for connection "%s" were not found' % label
        )

    options.update(kwargs)
    return django.core.mail.get_connection(**options)


def send_email_partner(
    fail_silently=False, connection=None,
):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), send
    each message to each recipient list. Return the number of emails sent.
    """
    mailing = get_partner_active()

    connection = get_connection()

    mail_from = os.getenv("EMAIL_USER")
    messages = []

    for idx, row in mailing.iterrows():
        subject = f'Informe de dados Infodengue SE{last_week}'
        body = render_to_string(
            "email_secretarias.txt",
            context={"name": row['contact'], "context_message": last_week},
        )
        message = EmailMultiAlternatives(
            subject, body, mail_from, [row['email']]
        )
        logging.info(f"Enviando email para: {row['email']},")
        # message.attach_alternative(html, 'text/html')
        fp = open(
            os.path.join(
                settings.STATICFILES_DIRS[0], 'img/logo_signature.png'
            ),
            'rb',
        )
        msg_img = MIMEImage(fp.read())
        fp.close()
        # msg_img.add_header('Content-ID', '<{}>'.format("logo_signature.png"))
        message.attach(msg_img)
        messages.append(message)

    return connection.send_messages(messages)

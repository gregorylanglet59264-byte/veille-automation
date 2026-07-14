import smtplib, base64, uuid, datetime
from email.utils import formatdate

gmail_email = 'langlet.gregory@gmail.com'
gmail_password = 'vwewsvwuindvtzif'
recipients = ['gregory.langlet@sfr.fr', 'langlet.gregory@gmail.com']

# Simule le pire cas : BOM + accents dans le HTML
html = '\ufeff<html><body><h1>Test RAW MIME \u00e9\u00e0</h1><p>BOM + accents ok.</p></body></html>'
html = html.replace('\ufeff', '').replace('\ufffe', '')

boundary = uuid.uuid4().hex
filename = f'veille_{datetime.datetime.now().strftime("%Y_%m_%d")}.html'
date_ascii = datetime.datetime.now().strftime('%Y-%m-%d')

# Tout en base64 → 100% ASCII garanti
html_b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
text_b64 = base64.b64encode('Rapport en piece jointe.'.encode('utf-8')).decode('ascii')

raw = (
    f'From: Gregory LANGLET <{gmail_email}>\r\n'
    f'To: {", ".join(recipients)}\r\n'
    f'Subject: TEST RAW MIME - Veille {date_ascii}\r\n'
    f'Date: {formatdate(localtime=True)}\r\n'
    f'MIME-Version: 1.0\r\n'
    f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n'
    f'\r\n'
    f'--{boundary}\r\n'
    f'Content-Type: text/plain; charset=utf-8\r\n'
    f'Content-Transfer-Encoding: base64\r\n'
    f'\r\n'
    f'{text_b64}\r\n'
    f'\r\n'
    f'--{boundary}\r\n'
    f'Content-Type: text/html; charset=utf-8; name="{filename}"\r\n'
    f'Content-Disposition: attachment; filename="{filename}"\r\n'
    f'Content-Transfer-Encoding: base64\r\n'
    f'\r\n'
    f'{html_b64}\r\n'
    f'\r\n'
    f'--{boundary}--\r\n'
)

with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(gmail_email, gmail_password)
    server.sendmail(gmail_email, recipients, raw.encode('ascii'))
print('OK - RAW MIME envoye !')

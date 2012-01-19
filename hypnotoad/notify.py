#
# Common ways to notify remote locations.
#

import smtplib

from email.mime.text import MIMEText

class notify(object):
    def email(self, to_list, message, subject="[hypnotoad] Notification", from_address="nobody@nowhere", smtp_server="mail.lanl.gov"):
        email = MIMEText(message)

        email['Subject'] = subject
        email['From'] = from_address
        email['To'] = ', '.join(to_list)

        s = smtplib.SMTP(smtp_server)
        s.sendmail(from_address, to_list, email.as_string())
        s.quit()

# EOF

#
# Common ways to notify remote locations.
#

import logging
import smtplib

from email.mime.text import MIMEText

LOG = logging.getLogger('root')

class notify(object):
    def email(self, to_list, message, subject="Notification", from_address="nobody@nowhere", smtp_server="pobox1663.lanl.gov"):
        LOG.debug("Sending an email.")

        email = MIMEText(message)

        email['Subject'] = "[hypnotoad] " + str(subject)
        email['From'] = from_address
        email['To'] = ', '.join(to_list)

        s = smtplib.SMTP(smtp_server)
        s.sendmail(from_address, to_list, email.as_string())
        s.quit()

# EOF

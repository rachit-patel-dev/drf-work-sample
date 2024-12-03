from django.conf import settings
from django.core.mail import EmailMessage
from utils.django.exceptions import MailNotSendException, TemplateNotFoundException


class Mail(EmailMessage):
    """
    A class representing an email message.

    Attributes:
        subject (str): The subject of the email message.
        body (str): The body of the email message.
        from_email (str): The sender's email address.
        to (list): A list of recipient email addresses.
        dynamic_template_data (dict): A dictionary of dynamic template data.
        template_id (str): The ID of the email template.

    Methods:
        set_mail_data(subject="", body="", from_email=None, to=[], dynamic_template_data=None, template_id=None):
            Set the data for the email message.
    """

    def __init__(
        self,
        subject="",
        body="",
        from_email=None,
        to=None,
        bcc=None,
        connection=None,
        attachments=None,
        headers=None,
        cc=None,
        reply_to=None,
    ):
        super().__init__(
            subject,
            body,
            from_email,
            to,
            bcc,
            connection,
            attachments,
            headers,
            cc,
            reply_to,
        )

    def set_mail_data(
        self,
        subject="",
        body="",
        from_email=None,
        to=[],
        dynamic_template_data=None,
        template_id=None,
    ):
        """
        Set the data for the email message.

        Parameters:
            subject (str): The subject of the email message. Defaults to an empty string.
            body (str): The body of the email message. Defaults to an empty string.
            from_email (str): The sender's email address. Defaults to None.
            to (list): A list of recipient email addresses. Defaults to an empty list.
            dynamic_template_data (dict): A dictionary of dynamic template data. Defaults to None.
            template_id (str): The ID of the email template. Defaults to None.
        """
        self.subject = subject
        self.body = body
        self.from_email = from_email
        self.to = to
        self.dynamic_template_data = dynamic_template_data
        self.template_id = template_id


class MailerServices:
    def __init__(self):
        self.log = log
        self.from_email = settings.EMAIL_FROM_ADDRESS

    def set_mail_instance(self):
        self.mail_instance = Mail()

    def send_mail(
        self,
        email: str,
        subject: str,
        template_data: dict,
        template_name: str,
        language: str = settings.DEFAULT_GERMAN_LANGUAGE,
    ):
        """
        This function fetched template_id with different language and name of templates

        parameters:
            template_name:
                required, When we have to filter email template based on company_general_settings language (here, default language is German.)

            language : required, while filtering using template_name

        """
        if settings.ENABLE_MAILS:
            try:
                template_selection = settings.SENDGRID_TEMPLATES.get(template_name)
                template_id = template_selection.get(language.lower())

                if not template_id:
                    self.log.error("Template_id not found for selected language")
                    raise TemplateNotFoundException(
                        "template-not-found", f"Template Not Found, {str(e)}", self.log
                    )

                self.set_mail_instance()
                self.mail_instance.set_mail_data(
                    subject=subject,
                    from_email=self.from_email,
                    to=[email],
                    template_id=template_id,
                    dynamic_template_data=template_data,
                )
                self.mail_instance.send(fail_silently=False)
            except Exception as e:
                self.log.error(str(e))
                raise MailNotSendException("mail-not-send-exception", str(e), self.log)
        else:
            self.log.info(f"{template_data}-send-email-data-for-{email}")

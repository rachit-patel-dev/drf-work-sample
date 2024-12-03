# Mail and MailerServices Classes - Email Sending in Django

## Description

The code snippet defines a class called `Mail` that extends the `EmailMessage` class from Django. It also introduces a class called `MailerServices`. The `Mail` class represents an email message and has methods to set the data for the email. The `MailerServices` class has a method called `send_mail` that sends an email using the `Mail` class.

## Inputs

- **subject (str):** The subject of the email message.
- **body (str):** The body of the email message.
- **from_email (str):** The sender's email address.
- **to (list):** A list of recipient email addresses.
- **dynamic_template_data (dict):** A dictionary of dynamic template data.
- **template_id (str):** The ID of the email template.
- **email (str):** The recipient's email address.
- **template_data (dict):** The data to be used in the email template.
- **template_name (str):** The name of the email template.
- **language (str):** The language to be used for the email template.

## Flow

1. The `Mail` class is defined with attributes for the email message data and a method to set the data.
2. The `MailerServices` class is defined with a method called `send_mail` that takes in the necessary parameters for sending an email.
3. If email sending is enabled in the settings, the method fetches the template ID based on the template name and language.
4. If the template ID is not found, an exception is raised.
5. An instance of the `Mail` class is created, and the email message data is set.
6. The email is sent using the `send` method of the `Mail` instance.
7. If there is an error during the email sending process, an exception is raised.

## Outputs

None

## Usage Example

```python
# Create an instance of MailerServices
mailer = MailerServices()

# Send an email using the MailerServices class
mailer.send_mail(
    email="example@example.com",
    subject="Hello",
    template_data={"name": "John"},
    template_name="welcome_email",
    language="en"
)
```

This example sends an email to the specified email address with the subject "Hello" using the "welcome_email" template in English. The template data includes a variable "name" with the value "John".
```
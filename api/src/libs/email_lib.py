import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

class Email:
    receiver: str = ''
    sender: str = ''
    sender_name: str = 'Shipped Brain'
    server: smtplib.SMTP = None

    def __init__(self):
        try:
            self.sender = os.getenv('EMAIL_ADDRESS')
            self.server = smtplib.SMTP_SSL(os.getenv('EMAIL_SMTP_HOST'), os.getenv('EMAIL_SMTP_PORT'))
            self.server.ehlo()
            self.server.login(self.sender, os.getenv('EMAIL_PASSWORD'))
        except Exception as e:
            print('[INIT EXCEPTION]: ', str(e))

    def send_email(self, subject: str, html: str):
        '''
            Set email info and send it
        '''

        msg = MIMEMultipart('alternative')

        msg['Subject'] = subject
        msg['FROM'] = self.sender
        msg['To'] = self.receiver

        self.subject = subject

        part = MIMEText(html, 'html')

        msg.attach(part)
        self.server.sendmail(self.sender, self.receiver, msg.as_string())
        self.server.quit()

    def send_test_email(self):
        '''
            Send test email
        '''

        self.receiver = os.getenv('EMAIL_TEST')

        subject = 'Shipped Brain - Test Email'

        content = f"""
        <h3>Hi SB,</h3>
        <p>Email is working correctly!</p>
        <br>
        """

        self.send_email(subject = subject, html = self.format_email(content = content))

    def send_password_reset_email(self, user_name: str, user_email: str, reset_token: str):
        '''
            Send email for account password reset
        '''

        self.receiver = user_email

        reset_url = f"{os.getenv('CLIENT_URL')}/reset-password/{reset_token}"
        subject = 'Shipped Brain - New password reset request'

        content = f"""
        <h3>Hi {user_name.split(' ')[0]},</h3>
        <p>You've recently requested a password reset for your Shipped Brain account. By clicking the button below you'll be redirected to a page where you'll able to do so by following the instructions on the screen.</p>
        <br>
        <a href={reset_url} style='width: 220px; padding: 15px; text-align: center; background-color: #e0115f; color: #fff; text-decoration: none; font-weight: bold; font-size: 15px;'>Reset your password</a>
        <br>
        <br>
        <p>If this request wasn't made by you, please let us know by replying to this email.</p>
        """

        self.send_email(subject = subject, html = self.format_email(content = content))

    def send_feature_access_request_email(self, user_name: str, user_email: str, feature_name: str):
        '''
            Send email when user requests access to a feature
        '''

        self.receiver = user_email
        subject = f'Shipped Brain - Request to access {feature_name} feature'

        content = f"""
            <h3>Hi {user_name.split(' ')[0]},</h3>
            <p>We've received your request to access the <b>{feature_name.lower()}</b> feature.</p>
            <p>You'll receive an email from our team soon confirming access was granted so you can start creating in no time!</p>
            <br>
            <br>
            <p>If this request wasn't made by you, please let us know by replying to this email.</p>
        """

        self.send_email(subject = subject, html = self.format_email(content = content))

    def send_feature_access_request_email_to_admin(self, user_name: str, user_email: str, feature_name: str, feature_reason: str):
        '''
            Send email to SB when user requests access to a feature
        '''

        self.receiver = self.sender
        subject = f'Shipped Brain - New request to access {feature_name} feature'

        content = f"""
            <h3>Hi SB,</h3>
            <p>A new request to access the <b>{feature_name.lower()}</b> feature was made by {user_name} (<a href="mailto:{user_email}">{user_email}</a>).</p>
            <p>"{feature_reason}"</p>
        """

        self.send_email(subject = subject, html = self.format_email(content = content))

    def send_account_created_email(self, user_name: str, user_email: str):
        '''
            Send email when user creates a new account
        '''
        
        self.receiver = user_email
        first_name = user_name.split(' ')[0]
        subject = f'Shipped Brain - Welcome {first_name}'
        content = f"""
            <h3>Hi {first_name},</h3>
            <p>Welcome to Shipped Brain!</p>
            <p>Whether you're a Data Scientist, app developer or anything in between, you've taken a great step forward when it comes to advancing AI!</p>
            <p style='font-weight: bold;'>Here are some ways you can get started using Shipped Brain:</p>
            <a href='{os.getenv('CLIENT_URL')}/deploy' style='color: #e0115f; text-decoration: none; font-weight: bold; font-size: 15px;'>Deploy a model</a>
            <br>
            <a href='{os.getenv('CLIENT_URL')}/requests' style='color: #e0115f; text-decoration: none; font-weight: bold; font-size: 15px;'>Request a model</a>
            <br>
            <br>
            <a href={os.getenv('CLIENT_URL')} style='width: 220px; padding: 15px; text-align: center; background-color: #e0115f; color: #fff; text-decoration: none; font-weight: bold; font-size: 15px;'>Explore</a>
            <br>
            <br>
        """

        self.send_email(subject = subject, html = self.format_email(content = content))

    def send_deployed_model_email(self, user_name: str, user_email: str, model_name: str, model_version: int):
        '''
            Send email when user deploys a model
        '''

        self.receiver = user_email
        subject = f'Shipped Brain - {model_name} v{model_version} model deployed'

        content = f"""
            <h3>Hi {user_name.split(' ')[0]},</h3>
            <p>Your model <b>{model_name} v{model_version}</b> was successfully deployed!</p>
            <p>Take a look at it using the button below.</p>
            <br>
            <a href="{os.getenv('CLIENT_URL')}/models/{model_name}/{model_version}" style='width: 220px; padding: 15px; text-align: center; background-color: #e0115f; color: #fff; text-decoration: none; font-weight: bold; font-size: 15px;'>{model_name}</a>
            <br>
            <br>
            <p>Thank you for choosing Shipped Brain!</p>
        """

        self.send_email(subject = subject, html = self.format_email(content = content))

    def send_failed_deployed_model_email(self, user_name: str, user_email: str, deployment_id: int):
        '''
            Send email when user deploys a model
        '''

        self.receiver = user_email
        subject = f'Shipped Brain - Failed to deploy model'

        content = f"""
               <h3>Hi {user_name.split(' ')[0]},</h3>
               <p>Your model deployment with id <b>{deployment_id}</b> could not be deployed!</p>
               <p>Please check your model's integrity.</p>
               <br>
               <br>
               <p>Thank you for choosing Shipped Brain!</p>
           """

        self.send_email(subject=subject, html=self.format_email(content=content))

    def send_first_time_model_used_email(self, user_name: str, user_email: str, model_name: str, model_version: int):
        '''
            Send email when model is used for the first time
        '''

        self.receiver = user_email
        subject = f'Shipped Brain - Your model {model_name} v{model_version} was used'

        content = f"""
            <h3>Hi {user_name.split(' ')[0]},</h3>
            <p>Your model <b>{model_name} v{model_version}</b> was just used for the first time!</p>
            <p>Way to get noticed!</p>
            <p>We encourage you to share it with your network to get even more visibility, let others know about your work.</p>
            <br>
            <a href="{os.getenv('CLIENT_URL')}/models/{model_name}/{model_version}" style='width: 220px; padding: 15px; text-align: center; background-color: #e0115f; color: #fff; text-decoration: none; font-weight: bold; font-size: 15px;'>{model_name}</a>
            <br>
            <br>
            <p>Thank you for your trust!</p>
        """

        self.send_email(subject = subject, html = self.format_email(content = content))
    
    def send_new_model_like_email(self, user_name: str, user_email: str, model_name: str):
        '''
            Send email when model receives a new like
        '''

        self.receiver = user_email
        subject = f'Shipped Brain - Your model {model_name} is getting hits!'

        content = f"""
            <h3>Hi {user_name.split(' ')[0]},</h3>
            <p>Your model <b>{model_name}</b> just received a new like!</p>
            <br>
            <a href="{os.getenv('CLIENT_URL')}/models/{model_name}" style='width: 220px; padding: 15px; text-align: center; background-color: #e0115f; color: #fff; text-decoration: none; font-weight: bold; font-size: 15px;'>Go to model</a>
            <br>
            <br>
        """

        self.send_email(subject = subject, html = self.format_email(content = content))
    
    def send_new_model_comment_email(self, model_owner_email: str, model_owner_name: str, model_name: str, commenter_name: str, comment: str):
        '''Send email when model gets a new comment

        :param model_owner_email: Receiver's email
        :param model_owner_name: Receiver's name
        :param model_name: Model that was commented on
        :param commenter_name: Commenter's name
        :param comment: Comment's content
        '''

        self.receiver = model_owner_email
        subject = f'Shipped Brain - New comment on {model_name}'

        content = f"""
            <h3>Hi {model_owner_name.split(' ')[0]},</h3>
            <p>{commenter_name} commented the following on your model <b>{model_name}</b>.</p>
            <p>
            <i>{comment}</i>
            </p>
            <br>
            <a href="{os.getenv('CLIENT_URL')}/models/{model_name}" style='width: 220px; padding: 15px; text-align: center; background-color: #e0115f; color: #fff; text-decoration: none; font-weight: bold; font-size: 15px;'>Go to model</a>
            <br>
            <br>
        """

        self.send_email(subject=subject, html=self.format_email(content=content))

    def format_email(self, content: str):
        '''
            Get email in ready to send format
        '''

        return f"""<html>
            <body>
                {content}
                <h4>Thanks,
                <br>
                Shipped Brain
                </h4>
            <body>
        </html>
        """

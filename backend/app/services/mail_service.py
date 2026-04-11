import random
from datetime import datetime, timedelta

class MailService:
    @staticmethod
    def send_otp(email, otp):
        """
        Simulate sending an OTP via email by printing it to the console.
        In a real app, this would use Flask-Mail or an API like Resend.
        """
        print("\n" + "="*50)
        print(f"📧 EMAIL SENT TO: {email}")
        print(f"🔑 YOUR OTP CODE IS: {otp}")
        print(f"🕒 EXPIRES IN: 10 Minutes")
        print("="*50 + "\n")
        return True

    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP."""
        return str(random.randint(100000, 999999))

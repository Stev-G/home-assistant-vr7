class UserDataService:

    def __init__(self, api_client):
        self.api = api_client

    async def send_otp_mail(self, email):
        await self.api.send_otp(email)

    async def validate_otp(self, email, otp):
        return await self.api.validate_otp(email, otp)
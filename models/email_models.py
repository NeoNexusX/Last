import os
from pydantic import BaseModel
from datetime import datetime



class EmailConfirmResponseBase(BaseModel):
    email: str
    send_time: datetime


# EmailRequest model
class EmailConfirmRequest(EmailConfirmResponseBase):
    subject: str = "Account Confirmation By Server"
    text_content: str
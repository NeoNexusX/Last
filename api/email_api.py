import os
from typing import Annotated
import httpx
from fastapi import HTTPException, Depends
from starlette import status
from logger import get_logger
from models.email_models import EmailConfirmResponseBase, EmailConfirmRequest

logger = get_logger("main.email-api")

email_send_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,  # 409 Conflict
    detail="Send Failed error by no reason",  # 明确提示用户已存在
)


async def send_simple_message(email_info: EmailConfirmResponseBase):
    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
    MAILGUN_API_URL = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

    request_data = EmailConfirmRequest.model_validate(
        {**email_info.model_dump(),
         "text_content": "Confirm your email"}
    )
    logger.info(request_data)
    logger.info(MAILGUN_API_KEY)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                MAILGUN_API_URL,
                auth=("api", MAILGUN_API_KEY),
                data={
                    "from": f"Mailgun Sandbox <postmaster@{MAILGUN_DOMAIN}>",
                    "to": request_data.email,
                    "subject": request_data.subject,
                    "text": request_data.text_content
                }
            )
            response.raise_for_status()  # 如果请求失败，抛出异常
            return EmailConfirmRequest

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text
            )
        except Exception as e:
            logger.error(e)
            raise email_send_exception


EmailConfirmDep = Annotated[EmailConfirmResponseBase, Depends(send_simple_message)]

from passlib.context import CryptContext
from io import BytesIO
from fastapi import status, HTTPException,Depends, APIRouter,UploadFile, File, Form
import boto3
from botocore.exceptions import NoCredentialsError
from config import settings
import uuid
import logging

import os
from passlib.context import CryptContext
from fastapi.responses import StreamingResponse
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


AWS_SERVER_PUBLIC_KEY = settings.AWS_SERVER_PUBLIC_KEY
AWS_SERVER_SECRET_KEY = settings.AWS_SERVER_SECRET_KEY

def hash(password:str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_pass):
    return pwd_context.verify(plain_password, hashed_pass)



async def upload_image_to_s3(file: UploadFile, bucket_name: str, file_name: str = None) -> str:
    s3 = boto3.client('s3', aws_access_key_id=AWS_SERVER_PUBLIC_KEY, aws_secret_access_key=AWS_SERVER_SECRET_KEY)
    try:
        # Generate unique filename if not provided
        unique_filename = file_name if file_name else f"{uuid.uuid4().hex}.jpg"
        
        # Read the file content
        contents = await file.read()
        file_obj = BytesIO(contents)

        # Upload the file to the S3 bucket
        s3.upload_fileobj(file_obj, bucket_name, unique_filename)

        # Construct the public URL for the uploaded image
        image_url = f"https://{bucket_name}.s3.amazonaws.com/{unique_filename}"
        
        # Reset file pointer for potential future reads
        await file.seek(0)
        
        return image_url

    except NoCredentialsError:
        logging.error("S3 credentials not available")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="S3 credentials not available")
    
    except Exception as e:
        logging.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error uploading image")

def generate_unique_filename(original_filename: str) -> str:
    ext = original_filename.split('.')[-1]  # Get the file extension
    unique_name = f"{uuid.uuid4()}.{ext}"  # Create a unique filename with the same extension
    return unique_name
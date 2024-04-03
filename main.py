from fastapi import FastAPI, Form, File, UploadFile, Request
from pydantic import EmailStr
from zipfile import ZipFile
import os
import uvicorn
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

DEBIAS_API_URL: str = os.getenv("DEBIAS_API_URL")
MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "do-not-reply@debias.eu")
MAIL_PORT = os.getenv("MAIL_PORT", 587)
MAIL_SERVER = os.getenv("MAIL_SERVER", "")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "")

conf = ConnectionConfig(
    MAIL_USERNAME = MAIL_USERNAME,
    MAIL_PASSWORD = MAIL_PASSWORD,
    MAIL_FROM = MAIL_FROM,
    MAIL_PORT = MAIL_PORT,
    MAIL_SERVER = MAIL_SERVER,
    MAIL_FROM_NAME = MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER='./templates/'
)

def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, body: dict):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype='html',
    )
    fm = FastMail(conf)
    background_tasks.add_task(
       fm.send_message, message, template_name='email.html')
app = FastAPI()


@app.get("/hello-world")
async def root():
    return {"message": "Hello World"}

def try_utf8(data):
    "Returns a Unicode object on success, or None on failure"
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
       return None
    
def parse_zip(uploaded_zip):
    texts = []
    filenames = []
    with ZipFile(uploaded_zip.file) as zf:
        for name in zf.namelist():
            if zf.getinfo(name).is_dir():
                continue
            with zf.open(name) as f:
                data = f.read()
                udata = try_utf8(data)
                if udata is None:
                    return {"error": "File not encoded with utf-8"}
                else:
                    # Handle unicode data
                    texts.append(udata)
                    filenames.append(name)
    return texts, filenames

from collections import deque


def divide_chunks(data, chunksize):
    """
    Divide an iterator into chunks of the given size.
    The last chunks might be smaller that the chunksize.

    :param data: Anything that iterates values
    :param chunksize: Size of the
    """
    data_iter = iter(data)
    buffer = deque()

    while True:
        try:
            buffer.append(next(data_iter))
        except StopIteration:
            break

        if len(buffer) == chunksize:
            yield list(buffer)
            buffer.clear()

    if buffer:
        yield list(buffer)

@app.post("/")
async def upload(
    language: str = Form(),
    user_email: EmailStr = Form(),
    debias_zip: UploadFile = File()
):
    # filename = debias_zip.filename
    texts, filenames = parse_zip(debias_zip)
    
    dereference_dict = dict(zip(texts, filenames))

    for chunk in divide_chunks(texts, 5):
        body = {
            "language": language,
            "values": chunk
        }

        # TODO here we will call debias api
    
    return dereference_dict

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
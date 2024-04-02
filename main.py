from fastapi import FastAPI, Form, File, UploadFile, Request
from pydantic import EmailStr
from zipfile import ZipFile

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
        print(chunk)
        # TODO here we will call debias api
    
    return dereference_dict
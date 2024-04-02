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

@app.post("/")
async def upload(
    language: str = Form(),
    user_email: EmailStr = Form(),
    debias_zip: UploadFile = File()
):
    # filename = debias_zip.filename
    texts, filenames = parse_zip(debias_zip)
    
    dereference_dict = dict(zip(texts, filenames))
    
    return dereference_dict
import os
import time
import hashlib
from enum import Enum
from flask import Flask

ALLOWED_EXTENSIONS = {".jpg", ".png", ".jpeg"}
BUF_SIZE = 65536

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["FULL_UPLOAD_FOLDER"] = os.path.join(__name__, app.config["UPLOAD_FOLDER"])


def initialize_app():
    full_upload_dir = os.path.join(__name__, app.config["UPLOAD_FOLDER"])
    if not os.path.exists(full_upload_dir):
        os.mkdir(full_upload_dir)


class ImageOption(Enum):
    SPLIT = 1
    FILL = 2


def calculate_uuid(stream):
    sha1 = hashlib.sha1()
    # No need to hash the entire file to create a UUID
    data = stream.read(BUF_SIZE)
    sha1.update(data)
    stream.seek(0)
    sha1.update(str(time.time_ns()).encode())
    return sha1.hexdigest()


def get_img_dir(uuid):
    return os.path.join(app.config["FULL_UPLOAD_FOLDER"], uuid)


initialize_app()

from .image_utils_app import *
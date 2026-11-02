"""Store files uploaded by users."""
import os

UPLOAD_DIR = 'uploads'


def save_upload(filename, data, user):
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, 'wb') as handle:
        handle.write(data)
    return {'path': path, 'owner': user}

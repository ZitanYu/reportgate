"""Store uploaded pastes on disk.

Sample code for reportgate's examples. The missing filename check in
save_upload() is intentional, so that an example report has something real
to point at. Do not deploy this code.
"""

import os

UPLOAD_DIR = "uploads"


def save_upload(filename, data, base_dir=UPLOAD_DIR):
    """Write an uploaded paste to disk and return the path it was written to."""
    os.makedirs(base_dir, exist_ok=True)
    target = os.path.join(base_dir, filename)
    with open(target, "wb") as handle:
        handle.write(data)
    return target


def load_paste(paste_id, base_dir=UPLOAD_DIR):
    """Read a stored paste by its numeric id."""
    if not paste_id.isdigit():
        raise ValueError("paste id must be numeric")
    with open(os.path.join(base_dir, paste_id), "rb") as handle:
        return handle.read()

# Path traversal in upload storage

**Severity:** high
**CWE:** CWE-22

## Summary

`save_upload()` in `pastebox/storage.py` joins the user-supplied filename onto the
upload directory without normalising it, so a filename containing `../` is written
outside the upload directory.

The `X-Filename` request header is passed straight to `save_upload()`, so the
filename is attacker-controlled.

## Affected code

`pastebox/storage.py:16`

```python
target = os.path.join(base_dir, filename)
with open(target, "wb") as handle:
```

## Steps to reproduce

1. Create an empty directory and change into it.
2. Run the snippet below with the repository root on `PYTHONPATH`.
3. Observe that the file is created next to the `uploads` directory, not inside it.

```python
from pastebox.storage import save_upload
print(save_upload("../outside.txt", b"x"))
```

## Expected

The filename is rejected, or confined to the upload directory.

# pastebox (sample project)

pastebox is a deliberately tiny sample project used by reportgate's examples. The
reports in `../reports` point at it.

It contains an **intentional** flaw (`save_upload()` in `pastebox/storage.py` does
not check the filename) so that one example report has something real to point at.
Do not deploy this code, and please do not report that flaw as a vulnerability in
reportgate.

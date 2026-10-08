# HTML injection in paste titles

CWE-79. Severity: medium.

The paste title is concatenated into HTML without escaping in
`pastebox/templates.py` (line 22):

```python
return "<h1>" + title + "</h1>"
```

Steps to reproduce:

1. Start the server.
2. Create a paste whose title is `<i>hello</i>`.
3. Open the paste page: the title is rendered in italics instead of as text.

Tested on pastebox 0.1.

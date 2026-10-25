# Publishing ZeroResp to PyPI

Not published yet. When ready:

1. Create a PyPI API token at https://pypi.org/manage/account/token/ (scope: project `zeroresp` after first upload, or entire account for the first release).
2. From a clean checkout of `main` at the release tag:

```bash
python -m pip install --upgrade build twine
python -m build
twine check dist/*
twine upload dist/*
```

3. Prefer Trusted Publishing (OIDC from GitHub Actions) over a long-lived token when you add a release workflow.

Version comes from `pyproject.toml` (`5.4.4`). Bump that before the next upload. Do not force-push tags.

# Publishing Guide for rest-to-mcp-adapter

This guide explains how to publish the `rest-to-mcp-adapter` package to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - Test PyPI: https://test.pypi.org/account/register/
   - Production PyPI: https://pypi.org/account/register/

2. **API Tokens**: Generate API tokens for authentication:
   - Test PyPI: https://test.pypi.org/manage/account/#api-tokens
   - Production PyPI: https://pypi.org/manage/account/#api-tokens

3. **Install Tools**:
   ```bash
   pip install --upgrade build twine
   ```

## Build the Package

1. **Clean previous builds**:
   ```bash
   rm -rf dist/ build/ *.egg-info
   ```

2. **Build distribution files**:
   ```bash
   python -m build
   ```

   This creates:
   - `dist/rest_to_mcp_adapter-X.Y.Z-py3-none-any.whl` (wheel)
   - `dist/rest_to_mcp_adapter-X.Y.Z.tar.gz` (source distribution)

3. **Verify the build**:
   ```bash
   ls -lh dist/
   twine check dist/*
   ```

## Test on Test PyPI (Recommended First)

1. **Upload to Test PyPI**:
   ```bash
   twine upload --repository testpypi dist/*
   ```

   When prompted:
   - Username: `__token__`
   - Password: Your Test PyPI API token (starts with `pypi-`)

2. **Test installation from Test PyPI**:
   ```bash
   # Create a test environment
   python -m venv test-env
   source test-env/bin/activate  # On Windows: test-env\Scripts\activate

   # Install from Test PyPI
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ rest-to-mcp-adapter

   # Test basic import
   python -c "from adapter import OpenAPILoader, ToolGenerator; print('Success!')"

   # Deactivate and clean up
   deactivate
   rm -rf test-env
   ```

## Publish to Production PyPI

1. **Upload to PyPI**:
   ```bash
   twine upload dist/*
   ```

   When prompted:
   - Username: `__token__`
   - Password: Your PyPI API token (starts with `pypi-`)

2. **Verify the upload**:
   - Visit: https://pypi.org/project/rest-to-mcp-adapter/
   - Check that the README renders correctly
   - Verify all metadata is correct

3. **Test installation**:
   ```bash
   # In a new environment
   pip install rest-to-mcp-adapter
   python -c "from adapter import OpenAPILoader, ToolGenerator; print('Installed successfully!')"
   ```

## Version Management

### Updating the Version

Before each release, update the version in `pyproject.toml`:

```toml
[project]
name = "rest-to-mcp-adapter"
version = "X.Y.Z"  # Update this
```

### Version Numbering (Semantic Versioning)

- **X.Y.Z** where:
  - **X** (Major): Breaking changes, incompatible API changes
  - **Y** (Minor): New features, backwards-compatible
  - **Z** (Patch): Bug fixes, backwards-compatible

Examples:
- `0.1.0` → `0.1.1`: Bug fix
- `0.1.0` → `0.2.0`: New feature
- `0.9.0` → `1.0.0`: First stable release

### Release Workflow

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG** (if you have one)
3. **Commit changes**:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to X.Y.Z"
   ```
4. **Tag the release**:
   ```bash
   git tag -a vX.Y.Z -m "Release version X.Y.Z"
   git push origin main --tags
   ```
5. **Build and publish** (steps above)

## Using GitHub Actions (Optional)

You can automate publishing with GitHub Actions. Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add your PyPI API token to GitHub Secrets:
- Go to: Repository Settings → Secrets and variables → Actions
- Add secret: `PYPI_API_TOKEN` with your PyPI API token

## Troubleshooting

### "File already exists" error
- You cannot re-upload the same version
- Increment the version number and rebuild

### Import errors after installation
- Check that the `adapter` package is properly included
- Verify `pyproject.toml` has correct `packages = ["adapter"]` in `[tool.hatch.build.targets.wheel]`

### README not rendering on PyPI
- Ensure `readme = "README.md"` is in `pyproject.toml`
- Verify README uses standard Markdown (not GitHub-specific features)
- Run `twine check dist/*` to validate

### Missing dependencies
- Check that all dependencies are listed in `pyproject.toml` under `dependencies`
- Test in a clean virtual environment

## Maintenance Checklist

Before each release:

- [ ] Update version in `pyproject.toml`
- [ ] Run tests: `pytest`
- [ ] Update documentation
- [ ] Clean old builds: `rm -rf dist/ build/ *.egg-info`
- [ ] Build: `python -m build`
- [ ] Check build: `twine check dist/*`
- [ ] Test on Test PyPI (optional but recommended)
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] Create GitHub release with tag
- [ ] Verify installation: `pip install rest-to-mcp-adapter`
- [ ] Update announcement channels

## Resources

- **PyPI Package Page**: https://pypi.org/project/rest-to-mcp-adapter/
- **Python Packaging Guide**: https://packaging.python.org/
- **Twine Documentation**: https://twine.readthedocs.io/
- **Semantic Versioning**: https://semver.org/

---

For questions or issues, contact: Pawneet Singh

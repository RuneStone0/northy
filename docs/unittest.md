# Testing
## Full test before deployment
```
python -m pytest -c tests/pytest.ini -n auto
coverage-badge -o tests/report/coverage-badge.svg
```

## Other options
Run specific test:
```
python -m pytest -c tests/pytest.ini -n 0 .\tests\test_saxo.py::test_price
```

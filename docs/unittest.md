# Run all test cases
```
python -m pytest -c tests/pytest.ini
```

### Run all test cases for a file
```
python -m pytest -v --cov=northy --capture=no --cov-report=html --cov-report=term-missing:skip-covered --cov-append --cov-report=html:tests/report tests/test_utils.py
```

### Run specific function within test file
```
python -m pytest -v --cov=northy --capture=no --cov-report=html --cov-report=term-missing:skip-covered --cov-append --cov-report=html:tests/report tests/test_db.py::test_backup
```

### Drop console output by removing
```
--capture=no
```
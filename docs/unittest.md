# Run all test cases
```
python -m pytest -c tests/pytest.ini
```

### Test specific file, while overriding a few settings from pytest.ini
```
python -m pytest -c tests/pytest.ini -n 0 tests\test_config.py
```

### Run specific function within test file
```
python -m pytest -v --cov=northy --capture=no --cov-report=html --cov-report=term-missing:skip-covered --cov-append --cov-report=html:tests/report tests/test_db.py::test_backup
```

### Drop console output by removing
```
--capture=no
```
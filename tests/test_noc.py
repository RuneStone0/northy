import os
import shutil
from northy.noc import Noc

def test_process_notification():
    # create /tmp if not exists
    if not os.path.exists('/tmp'): os.makedirs('/tmp')

    filename = 'wpndatabase.db'
    original_path = f'tests/noc/{filename}'
    temp_path = f'/tmp/{filename}'
    # copy wpndatabase.sqlite to /tmp
    shutil.copy2(original_path, temp_path)

    # Test against temp file
    noc = Noc(production=False, wpndatabase_path=temp_path)
    assert noc.process_notification() == None

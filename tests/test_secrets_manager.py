from os import remove
from os.path import join
import pytest
import tempfile
from northy.secrets_manager import SecretsManager

@pytest.fixture
def temp_folder():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

def test_generate_key(temp_folder):
    sm = SecretsManager()

    # File paths
    mock_folder = 'tests/mock_data/secrets_manager'
    unencrypted_file = f'{mock_folder}/config.ini'
    key = join(temp_folder, '.key')
    encrypted_file = join(temp_folder, 'config.encrypted')

    # Generate key
    sm.generate_key(filename=key)

    # Encrypt
    sm.encrypt(file_in=unencrypted_file, file_out=encrypted_file, aes_key=key)

    # Encrypt without specifying file_out & cleanup after test
    sm.encrypt(file_in=unencrypted_file, aes_key=key)
    remove(join(f'{mock_folder}/config.encrypted'))

    # Read encrypted file
    sm.read(file=encrypted_file, aes_key=key)

    # Get encrypted data as dict
    output = sm.get_dict()

    assert isinstance(output, dict)
    assert output.get("SECTION", {}).get("MYKEY") == "MYSECRET"

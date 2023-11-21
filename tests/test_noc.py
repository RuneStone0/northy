import os
import shutil
from northy.noc import Noc

def test_process_notification():
    # create /tmp if not exists
    if not os.path.exists('/tmp'): os.makedirs('/tmp')

    files = [
        'wpndatabase.db',  # contains only tweets
        'wpndatabase-surfacex.db',  # contains no tweets (important for testing)
        'wpndatabase-windows10.db'
    ]
    for file in files:
        original_path = f'tests/noc/{file}'
        temp_path = f'/tmp/{file}'
        # copy wpndatabase.sqlite to /tmp
        shutil.copy2(original_path, temp_path)

        # Test against temp file
        noc = Noc(production=False, wpndatabase_path=temp_path)
        assert noc.process_notification() == None

def test_notification_to_tweet():
    # Test parsing notification without text (image posted)
    # Example: https://twitter.com/elonmusk/status/1727011989661397193
    toast = {'@launch': '0|0|Default|0|https://twitter.com/|p#https://twitter.com/#1tweet-1727011989661397193', '@displayTimestamp': '2023-11-21T17:13:21Z', 'visual': {'binding': {'@template': 'ToastGeneric', 'text': ['Elon Musk', None, {'@placement': 'attribution', '#text': 'twitter.com'}], 'image': {'@placement': 'appLogoOverride', '@src': 'C:\\Users\\rtk\\AppData\\Local\\Google\\Chrome\\User Data\\Notification Resources\\944d5e12-3a00-47a5-82fd-9f79f7f027ef.tmp', '@hint-crop': 'none'}}}, 'actions': {'action': {'@content': 'Go to Chrome notification settings', '@placement': 'contextMenu', '@activationType': 'foreground', '@arguments': '2|0|Default|0|https://twitter.com/|p#https://twitter.com/#1tweet-1727011989661397193'}}}
    mock_notification = { "payload": { "toast": toast } }
    noc = Noc(production=False, wpndatabase_path='tests/noc/wpndatabase.db')
    noc.notification_to_tweet(mock_notification)
    assert noc.notification_to_tweet(mock_notification)["from"] == 'Elon Musk'
    assert noc.notification_to_tweet(mock_notification)["text"] == ''
    
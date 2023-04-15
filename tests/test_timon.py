import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_readdb():
    from northy import timon
    t = timon.Timon()

    assert t.readdb(username="NTLiveStream") == None
    assert t.readdb(username="NTLiveStream") == None
    assert t.readdb(username="NTLiveStream", limit=1) == None
    assert t.readdb(username="NTLiveStream", limit=7) == None

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_fetch():
    from northy import timon
    t = timon.Timon()

    assert isinstance(t.fetch(), dict)
    assert isinstance(t.fetch(username="NTLiveStream"), dict)
    assert isinstance(t.fetch(username="NTLiveStream", limit=1), dict)
    assert isinstance(t.fetch(username="NTLiveStream", limit=2), dict)

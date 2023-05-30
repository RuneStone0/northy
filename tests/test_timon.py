import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_readdb():
    from northy.old import timon
    t = timon.Timon()

    assert t.readdb(username="NTLiveStream") == None
    assert t.readdb(username="NTLiveStream") == None
    assert t.readdb(username="NTLiveStream", limit=1) == None
    assert t.readdb(username="NTLiveStream", limit=7) == None

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_fetch():
    from northy.old import timon
    t = timon.Timon()

    assert isinstance(t.fetch(), list)
    assert isinstance(t.fetch(username="NTLiveStream"), list)
    assert isinstance(t.fetch(username="NTLiveStream", limit=1), list)
    assert isinstance(t.fetch(username="NTLiveStream", limit=2), list)

    assert "tid" in t.fetch(username="NTLiveStream", limit=1)[0]
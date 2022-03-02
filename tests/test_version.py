import emboa


class TestVersion(object):

    def test_version(self):
        v = emboa.__version__
        assert v == '0.1.0'

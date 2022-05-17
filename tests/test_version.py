import emperator


class TestVersion(object):

    def test_version(self):
        v = emperator.__version__
        assert v == '0.1.0'

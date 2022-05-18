import empack


class TestVersion(object):

    def test_version(self):
        v = empack.__version__
        assert v == '0.1.0'

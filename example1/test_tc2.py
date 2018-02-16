from Lib import putil



def test_before():
    putil.myassert(True, "test2")


def pytest_generate_tests(metafunc):
    # called once per each test function
    print("pytest_generate_tests %s" % (metafunc.function.__name__))
    try:
        metafunc.parametrize(['service'], [[1], [2]])
    except Exception as ex:
        print("skip creation tc %s" % ex)


class TestClass:

    def test_multi_assert(self, service, multi_assert):
        '''
        with multi_assert , all 3 assert will be executed
        '''
        putil.myassert(False, "test1")
        putil.myassert(True, "test2")
        putil.myassert(False, "test3")

    def test_default_assert(self, service):
        '''
        without multi_assert , test case abort after assert failed
        '''

        putil.myassert(True, "test1")
        putil.myassert(False, "test2")
        putil.myassert(True, "test3")

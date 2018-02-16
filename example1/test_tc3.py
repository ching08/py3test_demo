from Lib import putil


def pytest_generate_tests(metafunc):
    print("gereate_test for %s" % metafunc.function.__name__)
    idlist = []
    argvalues = []
    try:
        for scenario in metafunc.cls.scenarios:
            idlist.append(scenario[0])
            items = scenario[1].items()
            argnames = [x[0] for x in items]
            argvalues.append(([x[1] for x in items]))
        metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")
    except Exception as ex:
        print("funcation does not have scenarios %s : %s" % (metafunc.function.__name__, ex))


def make_scenarios(list):
    tmp = []
    for item in list:
        tmp.append((item, {'ch': item}))
    return tmp


def test_setup():
    assert True


class TestSample:

    scenarios = [('51', {'ch': '51'}), ('53', {'ch': '53'})]
    # scenarios=make_scenarios(['53','55'])

    def test_tc1(self, ch):
        print("ch is %s" % ch)
        assert isinstance(ch, str)

    def test_tc2(self, ch):
        print("ch is %s" % ch)
        assert isinstance(ch, str)

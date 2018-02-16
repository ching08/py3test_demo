import pytest
import os,shutil,sys
import logging
import termcolor
from Lib import putil
import ipdb
logging.basicConfig(filename='pytest.log',level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def tc_logger(request):
    '''
    fixure to provide auto tc log results creation.
    auto generte HTML report when test ended
    should be used globally for all tc
    '''

    print("--in tc_logger fixture")
   
    try:
        # if there is class
        tcName = "%s.%s.%s" % (request.module.__name__, request.cls.__name__, request.node.name)
    except Exception:
        # if there is no class
        tcName = "%s.%s" % (request.module.__name__, request.node.name)

    log_dir = os.environ.get('LOG_DEST_DIR', 'artifacts')
    tc_log_dir = os.path.join(log_dir, "tc_logs", putil.filename_escape('encode', tcName))
    tc_log_file = os.path.join(tc_log_dir, 'log_pytest.txt')
    logging.basicConfig(filename=tc_log_file,level=logging.INFO)
    os.makedirs(tc_log_dir)

    if sys.stdout.isatty():
        print(termcolor.colored("--TC_START %s" % tcName, 'yellow', 'on_blue', attrs=['bold', 'underline']))

    # redirect logging
   
    
    mylogger = logging.getLogger()
    myformat = logging.Formatter('%(asctime)s [%(levelname)s] %(name)-40s: %(message)s')
   
    # logging to file
    
    fh1 = logging.FileHandler(tc_log_file)
    fh1.setFormatter(myformat)
    mylogger.addHandler(fh1)
   

    # logging to stdout
    ch=logging.StreamHandler(sys.stdout)
    ch.setFormatter(myformat)
    logger.addHandler(ch)

    mylogger.info("--TC_START %s", tcName)
    mylogger.info("--Logfile: %s" % tc_log_file)
    mylogger.info("--DOC: %s" % request.function.__doc__)
   

    # mark current tc for testcase to use
    os.environ['TC_LOGGER_CURR_DIR'] = tc_log_dir

    # create doctr files
    docFile = os.path.join(tc_log_dir, "doc.txt")
    try:
        with open(docFile, 'w') as f:
            f.write(request.function.__doc__)
            
    except:
        pass

    def fin():
        print("Finishing tc_logger fixture")
        mylogger.removeHandler(fh1)
        mylogger.removeHandler(ch)
        
    request.addfinalizer(fin)


@pytest.fixture(scope='function')
def multi_assert(request, tc_logger):
    '''
    fixture to all multiple putil.myasserts multiple being called wihtout exist testcases
    test results will be auto-caculated when testcase exit
    good to use when we want to check multiple items in one testcases
    *MUST* be used with tc_logger fixture
    '''
    #print("--in  multi_assert fixture")

    # funcname = request.function.__name__

    if not os.environ.get('TC_LOGGER_CURR_DIR'):
        raise Exception("ERROR: multi_assert must be used together with tc_logger, please add tc_logger fixture")

    os.environ['MULTI_ASSERT'] = 'true'
    tc_err_file = os.path.join(os.environ['TC_LOGGER_CURR_DIR'], 'errMsg.txt')
    f = open(tc_err_file, 'w')
    f.close()

    def fin():

        os.environ['MULTI_ASSERT'] = 'false'
        # get error messages
        with open(tc_err_file, 'r') as f:
            errList = f.readlines()

        errMsg = ''.join(errList)
        if len(errList) > 0:
            logger.error("=" * 120)
            logger.error("Aggregrated ERRORS:\n%s" % errMsg)
            assert len(errList) == 0, errMsg

        else:
            putil.cprint("NO Aggregrated ERRORS for this testcases", color='green')
    request.addfinalizer(fin)


def pytest_runtest_makereport(item, call):
    '''
    fixture to mark testcase dependency on the previous testcase
    '''
    #print("--in  runtest_makereport")
    if "incremental" in item.keywords.keys():
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_runtest_setup(item):
    '''
    pair with runtest_makereport
    fixture to mark testcase dependency on the previous testcase
    '''
    print("--in  runtest_setup %s" % item.function.__name__)
    if "incremental" in item.keywords.keys():
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail("previous test failed (%s)" % previousfailed.name)


def pytest_configure(config):
    print("--in  pytest_config")
    log_dir = os.environ.get('LOG_DEST_DIR', 'artifacts')
    if os.path.exists(log_dir):
        logger.info("Remove directory '%s'", log_dir)
        shutil.rmtree(log_dir)


def pytest_unconfigure(config):

    print("--in pytest_unconfig")
    # junit report parser. trigger this only if tc_logger_fixture is in use
    if os.environ.get('TC_LOGGER_CURR_DIR'):
        if os.path.exists('pytest.log'):
            log_dir = os.environ.get('LOG_DEST_DIR', 'artifacts')
            print("copy pytest.log to " + os.path.join(log_dir, 'pytest.log'))
            shutil.copy2('pytest.log', os.path.join(log_dir, 'pytest.log'))
            os.remove('pytest.log')
        def junit_to_html():
            print("--parsing junit report...")
            log_dir = os.environ.get('LOG_DEST_DIR', 'artifacts')
            pwd = os.path.dirname(os.path.realpath(__file__))
            parser = os.path.join(pwd, 'Utils/junit_result_parser.py')
            cmd = "%s %s" % (parser, log_dir)
            (res,out) = putil.run_subprocess(cmd)
            print(out)
        config.add_cleanup(junit_to_html)



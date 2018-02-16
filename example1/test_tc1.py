import pytest
from Lib import putil
import logging

# apply tc_logger fixture to all functions



logger=logging.getLogger(__name__)

#@pytest.mark.usefixture("tc_logger")
class TestFixture:
    def test_tc1(self,tc_logger):
        '''
        demo without muti_assert, tc1 abrot on the 1st False assert
        '''
        logger.info("This test case 3 check points.testcase aborted on the 1st Failures assert")
        putil.myassert(False, "step 1 is False")
        putil.myassert(True, "Step2 is True")
        putil.myassert(False, "Step3 is False")


    def test_tc2(self,tc_logger,multi_assert):
        '''
        demo with muti_assert, tc3 does NOT abrot on the 1st False assert
        '''
        putil.myassert(False, "step 1 is False")
        putil.myassert(True, "Step2 is True")
        putil.myassert(False, "Step3 is False")


    @pytest.mark.parametrize("input1,input2", [(1, "x1"), (2, "x3"), (3, "x3")])
    def test_tc3(self,tc_logger,input1, input2):
        '''
        demo loop testcase with parameter
        '''
        putil.myassert(input1 == 2, "expecting parameter input1 %s == 2 " % input1)

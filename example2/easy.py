import pytest
from Lib import putil
import logging

logger=logging.getLogger(__name__)
myassert=putil.myassert

class Test1():
    
    @pytest.mark.parametrize("num",[(123),(-123),(-5360)])
    def test_reverse_integer(self,num):
        
        num1=''
        neg=1
        for c in str(num):
            if c =="-":
                neg=-1
                continue 

            num1=c+num1

        ans=int(num1)*neg
        logger.info("new number is %d" % ans)
        myassert(True,"result is %d" % ans)


        

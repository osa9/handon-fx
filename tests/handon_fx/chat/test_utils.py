#
# filename: `tests/handon_fx/chat/test_utils.py`
#

import unittest
import handon_fx.chat.utils as utils


# .
class UtilsTest(unittest.TestCase):

    #
    #
    #
    def setUp(self):
        pass

    def tearDown(self):
        pass

    #
    #
    #
    # .
    def test_buy_texts(self):
        exp = ['買', 'ロング', 'long', 'Long', 'L', 'buy', 'Buy']
        self.assertEqual(exp, utils.BUY_TEXTS)

    def test_summary_texts(self):
        exp = ['サマリ', 'summary', 'Summary', 'ポジション', 'Position', 'position', '残高', '余力']
        self.assertEqual(exp, utils.SUMMARY_TEXTS)

    # action.
    def test__find(self):

        #
        ret = utils._find(utils.BUY_TEXTS, '1L')
        exp = True
        self.assertEqual(exp, ret)

        #
        ret = utils._find(utils.BUY_TEXTS, 'USDJPY 1L')
        exp = True
        self.assertEqual(exp, ret)

        ret = utils._find(utils.BUY_TEXTS, 'USD/JPY 1L')
        exp = True
        self.assertEqual(exp, ret)

    # quantity.
    def test__find_n(self):

        ret = utils._find_n('1L')
        exp = [1.0]
        self.assertEqual(exp, ret)

        ret = utils._find_n('USDJPY 1L')
        exp = [1.0]
        self.assertEqual(exp, ret)

        ret = utils._find_n('USD/JPY 1L')
        exp = [1.0]
        self.assertEqual(exp, ret)

    # target object.
    def test__find_obj(self):

        ret = utils._find_obj('1L')
        exp = []
        self.assertEqual(exp, ret)

        #
        ret = utils._find_obj('USDJPY 1L')
        exp = ['USDJPY']
        self.assertEqual(exp, ret)

        ret = utils._find_obj('USD/JPY 1L')
        exp = ['USDJPY']
        self.assertEqual(exp, ret)

        ret = utils._find_obj('USD-JPY 1L')
        exp = ['USDJPY']
        self.assertEqual(exp, ret)

        ret = utils._find_obj('ドル円 1L')
        exp = ['USDJPY']
        self.assertEqual(exp, ret)



#
if __name__ == "__main__":
            unittest.main()

# endof filename: `tests/handon_fx/chat/test_utils.py`

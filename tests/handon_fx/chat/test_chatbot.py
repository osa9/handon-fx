#
# filename: `tests/handon_fx/test_chatbot.py`
#

import unittest
import handon_fx.fx as HandonFxAPI
import handon_fx.chat.chatbot as chatbot
import handon_fx.chat.utils as utils


# 
class ChatBotTest(unittest.TestCase):

    #
    #
    #
    def setUp(self):
        self.chatbot_default = chatbot.ChatBot(fxApi=HandonFxAPI)

    def tearDown(self):
        pass

    #
    #
    #
    def test__parse_text(self):

        ret = self.chatbot_default._parse_text(text= "1L")
        exp = {'operation': 'buy', 'size': 1.0}
        self.assertEqual(exp, ret)

        #
        ret = self.chatbot_default._parse_text(text= "USDJPY 1L")
        exp = {'operation': 'buy', 'pair': 'USDJPY', 'size': 1.0, }
        self.assertEqual(exp, ret)

        ret = self.chatbot_default._parse_text(text= "USD/JPY 1L")
        exp = {'operation': 'buy', 'pair': 'USDJPY', 'size': 1.0, }
        self.assertEqual(exp, ret)

    # FIXME: impl. the tests.
    def fixme_test_action(self):

        ret = ""
        exp = ['買', 'ロング', 'long', 'Long', 'L', 'buy', 'Buy']
        self.assertEqual(exp, ret)


#
if __name__ == "__main__":
            unittest.main()

# endof filename: `tests/handon_fx/test_chatbot.py`

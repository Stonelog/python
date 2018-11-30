import logging
import unittest
import os

logger = logging.getLogger(__name__)


class AlembicTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(AlembicTest, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_up_db(self):
        os.chdir("../../../")
        os.system("python -m alembic.config upgrade head")

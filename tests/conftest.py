import pytest
import os
import time
from run import app as flask_app
import contextlib
from tests import testingUtils
import random

#@pytest.fixture
#def test():
#    list_of_tests = os.listdir(TESTS_DIR)
#    random.shuffle(list_of_tests)
#    for file in list_of_tests:
#        next_test_file = os.path.join(TESTS_DIR, file)
#        yield testingUtils.executeTest(next_test_file)

# def pytest_addoption(parser):
#     parser.addoption('--repeat', action='store',
#         help='Number of tests to execute')


# def pytest_generate_tests(metafunc):
#     if metafunc.config.option.repeat is not None:
#         number_of_tests_to_execute = int(metafunc.config.option.repeat)

#         # We're going to duplicate these tests by parametrizing them,
#         # which requires that each test has a fixture to accept the parameter.
#         # We can add a new fixture like so:
#         metafunc.fixturenames.append('tmp_ct')

#         # Now we parametrize. This is what happens when we do e.g.,
#         # @pytest.mark.parametrize('tmp_ct', range(count))
#         # def test_foo(): pass
#         metafunc.parametrize('tmp_ct', range(number_of_tests_to_execute))

#@pytest.fixture
#def app():
#    yield flask_app


#@pytest.fixture
#def client(app):
#    return app.test_client()
#

#PID = None
#LISTE = []
#@contextlib.contextmanager
#def server():
#    global PID
#    PID = os.system('python run.py &')
#    yield
#    os.system('kill {}'.format(PID))


#@pytest.fixture
#def equipments():
#    with contextlib.ExitStack() as stack:
#        yield [stack.enter_context(server()) for port in ("C1", "C3", "C28")]
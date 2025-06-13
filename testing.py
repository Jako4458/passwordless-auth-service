from dotenv import load_dotenv
import os

if not load_dotenv(".env.testing"):
    print("ERROR LOADING TESTING ENVIRONMENT!")

import unittest
import testing.user_test as user_test

if __name__ == "__main__": 
    suite = unittest.defaultTestLoader.loadTestsFromModule(user_test)
    print(f"Amount of Tests: {suite.countTestCases()}") 
    print(suite)

    unittest.TextTestRunner(verbosity=2).run(suite)

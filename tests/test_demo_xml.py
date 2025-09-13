import unittest
from unittest.mock import patch
import sys
from io import StringIO
from multiconverter.converter5 import main


class TestConverter(unittest.TestCase):
    def setUp(self):
        # Wird vor jedem Test ausgeführt
        self.test_files = [ # (Filename, Exitcode)
            ("demo.xml", 0),
            ("demo_mcq_root.xml", 0),
            ("demo_err.xml", 1),
            ("demo_not_existant.xml", 1),
        ]

    def tearDown(self):
        # Wird nach jedem Test ausgeführt
        pass

    @patch('sys.exit')
    def test_help(self, mock_exit):
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            main([sys.argv[0]])

            # mock_exit.assert_called_once()  # Prüft, ob sys.exit() aufgerufen wurde
            mock_exit.assert_any_call(1)

            output = mock_stdout.getvalue()
        print(output)  # TODO: check output

    @patch('sys.exit')
    def test_basic_conversion(self, mock_exit):
        for i, (filename, exitcode) in enumerate(self.test_files):
            print(f"Testing '{filename}': {exitcode}")
            with patch('sys.stdout', new=StringIO()) as mock_stdout:
                main([sys.argv[0], f"output{i:02}.zip", filename])

                output = mock_stdout.getvalue()
                try:
                    # mock_exit.assert_called_once()  # Prüft, ob sys.exit() aufgerufen wurde
                    if 0 == exitcode:
                        mock_exit.assert_not_called()
                    else:
                        mock_exit.assert_any_call(exitcode)
                except AssertionError as e:
                    raise AssertionError(f"{e}\nDebug info:\n{output}")
            print(output) # TODO: check output


if __name__ == '__main__':
    unittest.main()
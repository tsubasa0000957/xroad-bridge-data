import unittest
from unittest.mock import Mock, call, patch

from scripts.investigations import fetch_bridges as target

class FetchPageTest(unittest.TestCase):
    def test_retries_connection_errors_then_succeeds(self):
        expected_page = {"result": ["success"]}

        success_response = Mock()
        success_response.raise_for_status.return_value = None
        success_response.json.return_value = expected_page

        with patch.object(target.requests, "get") as mock_get:
            mock_get.side_effect = [
                target.requests.ConnectionError("1回目の接続失敗"),
                target.requests.ConnectionError("2回目の接続失敗"),
                success_response,
            ]
            with patch.object(target.time, "sleep") as mock_sleep:
                actual_page = target.fetch_page(
                    "https://example.invalid",
                    {"offset": 0}
                )

                self.assertEqual(actual_page, expected_page)
                self.assertEqual(mock_get.call_count, 3)
                self.assertEqual(
                    mock_sleep.call_args_list,
                    [call(1), call(2)],
                )

    def test_retries_http_503_then_succeeds(self):
        retry_response = target.requests.Response()
        retry_response.status_code = 503
        retry_response.url = "https://example.invalid"

        expected_page = {"result": ["success"]}

        success_response = Mock()
        success_response.raise_for_status.return_value = None
        success_response.json.return_value = expected_page

        with patch.object(target.requests, "get") as mock_get:
            mock_get.side_effect = [
                retry_response,
                success_response,
            ]
            with patch.object(target.time, "sleep") as mock_sleep:
                actual_page = target.fetch_page(
                    "https://example.invalid",
                    {"offset": 0},
                )

                self.assertEqual(actual_page, expected_page)
                self.assertEqual(mock_get.call_count, 2)
                self.assertEqual(
                    mock_sleep.call_args_list,
                    [call(1)],
                )

    def test_does_not_retry_http_404(self):
        error_response = target.requests.Response()
        error_response.status_code = 404
        error_response.url = "https://example.invalid"

        with patch.object(
            target.requests,
            "get",
            return_value=error_response,
        ) as mock_get:
            with patch.object(target.time, "sleep") as mock_sleep:
                with self.assertRaises(target.requests.HTTPError):
                    target.fetch_page(
                        "https://example.invalid",
                        {"offset": 0},
                    )

                self.assertEqual(mock_get.call_count, 1)
                mock_sleep.assert_not_called()

    def test_raises_connection_error_after_max_attempts(self):
        connection_errors = [
            target.requests.ConnectionError("1回目の接続失敗"),
            target.requests.ConnectionError("2回目の接続失敗"),
            target.requests.ConnectionError("3回目の接続失敗"),
        ]

        with patch.object(
            target.requests,
            "get",
            side_effect=connection_errors,
        ) as mock_get:
            with patch.object(target.time, "sleep") as mock_sleep:
                with self.assertRaises(
                    target.requests.ConnectionError
                ) as raised_error:
                    target.fetch_page(
                        "https://example.invalid",
                        {"offset": 0},
                    )

                self.assertIs(
                    raised_error.exception,
                    connection_errors[-1],
                )
                self.assertEqual(mock_get.call_count, 3)
                self.assertEqual(
                    mock_sleep.call_args_list,
                    [call(1), call(2)],
                )
import os
from unittest.mock import MagicMock, patch

import pytest

from github_state import update_github_variable

ENV = {
    'GH_TOKEN': 'tok',
    'GITHUB_REPOSITORY': 'owner/repo',
    'GITHUB_ENVIRONMENT': 'goodvibrations',
}


class TestUpdateGithubVariable:
    def test_patch_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        with patch.dict(os.environ, ENV):
            with patch('github_state.requests.patch', return_value=mock_resp):
                update_github_variable('LAST_PUBLISHED_URL', 'https://example.com/ep1')

    def test_creates_variable_when_not_found(self):
        patch_resp = MagicMock()
        patch_resp.status_code = 404
        post_resp = MagicMock()
        post_resp.status_code = 201
        with patch.dict(os.environ, ENV):
            with patch('github_state.requests.patch', return_value=patch_resp):
                with patch('github_state.requests.post', return_value=post_resp):
                    update_github_variable('LAST_PUBLISHED_URL', 'https://example.com/ep1')

    def test_raises_on_api_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = 'Forbidden'
        with patch.dict(os.environ, ENV):
            with patch('github_state.requests.patch', return_value=mock_resp):
                with pytest.raises(RuntimeError, match='403'):
                    update_github_variable('LAST_PUBLISHED_URL', 'https://example.com/ep1')

    def test_raises_on_post_error_after_404(self):
        patch_resp = MagicMock()
        patch_resp.status_code = 404
        post_resp = MagicMock()
        post_resp.status_code = 422
        post_resp.text = 'Unprocessable'
        with patch.dict(os.environ, ENV):
            with patch('github_state.requests.patch', return_value=patch_resp):
                with patch('github_state.requests.post', return_value=post_resp):
                    with pytest.raises(RuntimeError, match='422'):
                        update_github_variable('LAST_PUBLISHED_URL', 'https://example.com/ep1')

    def test_raises_when_env_vars_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match='GH_TOKEN'):
                update_github_variable('LAST_PUBLISHED_URL', 'https://example.com/ep1')

    def test_raises_when_token_missing(self):
        env = {k: v for k, v in ENV.items() if k != 'GH_TOKEN'}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(RuntimeError, match='GH_TOKEN'):
                update_github_variable('LAST_PUBLISHED_URL', 'https://example.com/ep1')
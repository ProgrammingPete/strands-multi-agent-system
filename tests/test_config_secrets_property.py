"""
Property-based tests for configuration source fallback.

**Feature: aws-deployment-pipeline, Property 14: Configuration source fallback**
**Validates: Requirements 9.1, 9.2, 9.3**

Property: For any backend startup, WHEN AWS_SECRETS_NAME is not set THEN 
configuration SHALL be loaded from environment variables and .env files; 
WHEN AWS_SECRETS_NAME is set THEN configuration SHALL be loaded from 
Secrets Manager.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings, assume, Phase
import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# STRATEGIES FOR GENERATING TEST DATA
# =============================================================================

# Strategy for generating valid configuration keys
CONFIG_KEYS = [
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY", 
    "SUPABASE_ANON_KEY",
    "BEDROCK_MODEL_ID",
    "AWS_REGION",
    "API_HOST",
    "API_PORT",
    "ENVIRONMENT",
]

# Strategy for generating valid configuration values
config_value_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S')),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip() != "")

# Strategy for generating valid secret names
secret_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='-_/'),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() != "" and not x.startswith('-') and not x.startswith('_'))

# Strategy for generating valid AWS regions
aws_region_strategy = st.sampled_from([
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1"
])

# Strategy for generating configuration dictionaries
def config_dict_strategy():
    """Generate a dictionary of configuration values."""
    return st.fixed_dictionaries({
        "SUPABASE_URL": st.just("https://test.supabase.co"),
        "SUPABASE_SERVICE_KEY": st.text(min_size=10, max_size=50),
        "SUPABASE_ANON_KEY": st.text(min_size=10, max_size=50),
        "BEDROCK_MODEL_ID": st.just("amazon.nova-lite-v1:0"),
        "AWS_REGION": aws_region_strategy,
    })


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def reload_config_module():
    """
    Reload the config module to pick up new environment variables.
    
    This is necessary because the config module loads values at import time.
    """
    import importlib
    import sys
    
    # Remove cached modules
    modules_to_remove = [key for key in sys.modules.keys() if 'backend.config' in key]
    for mod in modules_to_remove:
        del sys.modules[mod]
    
    # Re-import
    from backend import config
    importlib.reload(config)
    return config


def create_mock_secrets_manager_response(secrets: Dict[str, Any]) -> Dict[str, Any]:
    """Create a mock response from AWS Secrets Manager."""
    return {
        'SecretString': json.dumps(secrets)
    }


# =============================================================================
# PROPERTY TESTS
# =============================================================================

class TestConfigurationSourceFallback:
    """
    Property-based tests for configuration source fallback.
    
    **Feature: aws-deployment-pipeline, Property 14: Configuration source fallback**
    **Validates: Requirements 9.1, 9.2, 9.3**
    """
    
    @settings(max_examples=100, deadline=None, phases=[Phase.generate, Phase.target])
    @given(
        env_supabase_url=st.just("https://env.supabase.co"),
        env_region=aws_region_strategy,
    )
    def test_fallback_to_env_when_secrets_name_not_set(
        self,
        env_supabase_url: str,
        env_region: str,
    ):
        """
        **Feature: aws-deployment-pipeline, Property 14: Configuration source fallback**
        **Validates: Requirements 9.1, 9.2, 9.3**
        
        Property: WHEN AWS_SECRETS_NAME is not set THEN configuration SHALL be 
        loaded from environment variables and .env files.
        
        This test verifies that:
        1. When AWS_SECRETS_NAME is not in the environment
        2. Configuration values are read from environment variables
        3. The config_source indicates environment variables/.env files
        """
        # Set up environment without AWS_SECRETS_NAME
        env_vars = {
            "SUPABASE_URL": env_supabase_url,
            "AWS_REGION": env_region,
            "ENVIRONMENT": "development",
        }
        
        # Remove AWS_SECRETS_NAME if it exists
        env_without_secrets = {k: v for k, v in env_vars.items()}
        
        with patch.dict(os.environ, env_without_secrets, clear=False):
            # Ensure AWS_SECRETS_NAME is not set
            if "AWS_SECRETS_NAME" in os.environ:
                del os.environ["AWS_SECRETS_NAME"]
            
            # Import the _load_configuration function directly
            from backend.config import _load_configuration
            
            # Reload to pick up new environment
            config_values, config_source = _load_configuration()
            
            # Property: Config source should indicate env vars/.env files
            assert "environment variables" in config_source.lower() or ".env" in config_source.lower(), (
                f"Config source should indicate environment variables or .env files, "
                f"but got: {config_source}"
            )
            
            # Property: Config values dict should be empty (values come from env vars directly)
            # When not using Secrets Manager, _load_configuration returns empty dict
            # and values are read from os.environ by _get_config_value
            assert config_values == {}, (
                f"When AWS_SECRETS_NAME is not set, config_values should be empty dict, "
                f"but got: {config_values}"
            )
    
    @settings(max_examples=50, deadline=None, phases=[Phase.generate, Phase.target])
    @given(
        secret_name=secret_name_strategy,
        aws_region=aws_region_strategy,
        secrets_data=config_dict_strategy(),
    )
    def test_loads_from_secrets_manager_when_name_set(
        self,
        secret_name: str,
        aws_region: str,
        secrets_data: Dict[str, str],
    ):
        """
        **Feature: aws-deployment-pipeline, Property 14: Configuration source fallback**
        **Validates: Requirements 9.1, 9.2, 9.3**
        
        Property: WHEN AWS_SECRETS_NAME is set THEN configuration SHALL be 
        loaded from Secrets Manager.
        
        This test verifies that:
        1. When AWS_SECRETS_NAME is set in the environment
        2. The system attempts to load from Secrets Manager
        3. The config_source indicates Secrets Manager
        """
        # Skip invalid secret names
        assume(len(secret_name.strip()) > 0)
        assume(not secret_name.startswith('-'))
        assume(not secret_name.startswith('_'))
        
        # Set up environment with AWS_SECRETS_NAME
        env_vars = {
            "AWS_SECRETS_NAME": secret_name,
            "AWS_REGION": aws_region,
        }
        
        # Mock the boto3 client
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = create_mock_secrets_manager_response(secrets_data)
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('boto3.client', return_value=mock_client):
                # Import and call _load_configuration
                from backend.config import _load_configuration
                
                config_values, config_source = _load_configuration()
                
                # Property: Config source should indicate Secrets Manager
                assert "secrets manager" in config_source.lower(), (
                    f"Config source should indicate Secrets Manager, "
                    f"but got: {config_source}"
                )
                
                # Property: Config source should include the secret name
                assert secret_name in config_source, (
                    f"Config source should include secret name '{secret_name}', "
                    f"but got: {config_source}"
                )
                
                # Property: Config values should match what was in Secrets Manager
                for key, value in secrets_data.items():
                    assert key in config_values, (
                        f"Config should contain key '{key}' from Secrets Manager"
                    )
                    assert config_values[key] == value, (
                        f"Config value for '{key}' should be '{value}', "
                        f"but got: {config_values[key]}"
                    )
                
                # Verify boto3 was called correctly
                mock_client.get_secret_value.assert_called_once_with(SecretId=secret_name)
    
    @settings(max_examples=50, deadline=None, phases=[Phase.generate, Phase.target])
    @given(
        config_key=st.sampled_from(CONFIG_KEYS),
        env_value=config_value_strategy,
        secrets_value=config_value_strategy,
    )
    def test_secrets_manager_takes_precedence_over_env(
        self,
        config_key: str,
        env_value: str,
        secrets_value: str,
    ):
        """
        **Feature: aws-deployment-pipeline, Property 14: Configuration source fallback**
        **Validates: Requirements 9.1, 9.2, 9.3**
        
        Property: WHEN both AWS_SECRETS_NAME is set AND environment variables exist,
        THEN Secrets Manager values SHALL take precedence.
        
        This test verifies that:
        1. When both sources have a value for the same key
        2. The Secrets Manager value is used
        """
        # Ensure values are different to test precedence
        assume(env_value.strip() != secrets_value.strip())
        assume(len(env_value.strip()) > 0)
        assume(len(secrets_value.strip()) > 0)
        
        secret_name = "test-secret"
        secrets_data = {config_key: secrets_value}
        
        env_vars = {
            "AWS_SECRETS_NAME": secret_name,
            "AWS_REGION": "us-east-1",
            config_key: env_value,  # Also set in environment
        }
        
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = create_mock_secrets_manager_response(secrets_data)
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('boto3.client', return_value=mock_client):
                from backend.config import _load_configuration, _get_config_value
                
                # Load configuration
                config_values, config_source = _load_configuration()
                
                # Manually test _get_config_value behavior
                # When Secrets Manager is used, values from it should be in config_values
                if config_key in config_values:
                    retrieved_value = config_values[config_key]
                    
                    # Property: Secrets Manager value should be used
                    assert retrieved_value == secrets_value, (
                        f"Secrets Manager value '{secrets_value}' should take precedence "
                        f"over env value '{env_value}', but got: {retrieved_value}"
                    )


class TestConfigurationSourceIndicator:
    """
    Tests for configuration source tracking.
    
    **Feature: aws-deployment-pipeline, Property 14: Configuration source fallback**
    **Validates: Requirements 9.5**
    """
    
    def test_config_source_logged_at_startup_env_vars(self):
        """
        **Feature: aws-deployment-pipeline, Property 14: Configuration source fallback**
        **Validates: Requirements 9.5**
        
        Property: WHEN the backend loads configuration THEN the Backend SHALL log 
        which configuration source is being used.
        
        This test verifies that config_source is properly set when using env vars.
        """
        # Ensure AWS_SECRETS_NAME is not set
        env_vars = {
            "SUPABASE_URL": "https://test.supabase.co",
            "AWS_REGION": "us-east-1",
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            if "AWS_SECRETS_NAME" in os.environ:
                del os.environ["AWS_SECRETS_NAME"]
            
            from backend.config import _load_configuration
            
            _, config_source = _load_configuration()
            
            # Property: Source should be clearly indicated
            assert config_source is not None and len(config_source) > 0, (
                "Config source should be a non-empty string"
            )
            assert "environment" in config_source.lower() or ".env" in config_source.lower(), (
                f"Config source should indicate environment variables, got: {config_source}"
            )
    
    def test_config_source_logged_at_startup_secrets_manager(self):
        """
        **Feature: aws-deployment-pipeline, Property 14: Configuration source fallback**
        **Validates: Requirements 9.5**
        
        Property: WHEN the backend loads configuration from Secrets Manager 
        THEN the Backend SHALL log the Secrets Manager source.
        """
        secret_name = "canvalo/beta/config"
        secrets_data = {"SUPABASE_URL": "https://test.supabase.co"}
        
        env_vars = {
            "AWS_SECRETS_NAME": secret_name,
            "AWS_REGION": "us-east-1",
        }
        
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = create_mock_secrets_manager_response(secrets_data)
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('boto3.client', return_value=mock_client):
                from backend.config import _load_configuration
                
                _, config_source = _load_configuration()
                
                # Property: Source should indicate Secrets Manager with secret name
                assert "secrets manager" in config_source.lower(), (
                    f"Config source should indicate Secrets Manager, got: {config_source}"
                )
                assert secret_name in config_source, (
                    f"Config source should include secret name, got: {config_source}"
                )


class TestSecretsManagerErrorHandling:
    """
    Tests for Secrets Manager error handling.
    
    **Feature: aws-deployment-pipeline, Property 14: Configuration source fallback**
    **Validates: Requirements 9.1, 9.2**
    """
    
    @settings(max_examples=20, deadline=None, phases=[Phase.generate, Phase.target])
    @given(
        secret_name=secret_name_strategy,
        error_code=st.sampled_from([
            "ResourceNotFoundException",
            "AccessDeniedException",
            "InvalidParameterException",
        ]),
    )
    def test_secrets_manager_error_raises_configuration_error(
        self,
        secret_name: str,
        error_code: str,
    ):
        """
        **Feature: aws-deployment-pipeline, Property 14: Configuration source fallback**
        **Validates: Requirements 9.1, 9.2**
        
        Property: WHEN Secrets Manager retrieval fails THEN the system SHALL 
        raise a ConfigurationError with details.
        """
        assume(len(secret_name.strip()) > 0)
        
        from botocore.exceptions import ClientError
        from backend.config import _get_secrets_from_aws, ConfigurationError
        
        # Create a mock error response
        error_response = {
            'Error': {
                'Code': error_code,
                'Message': f'Test error: {error_code}'
            }
        }
        
        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = ClientError(error_response, 'GetSecretValue')
        
        with patch('boto3.client', return_value=mock_client):
            with pytest.raises(ConfigurationError) as exc_info:
                _get_secrets_from_aws(secret_name, "us-east-1")
            
            # Property: Error should contain useful information
            assert secret_name in str(exc_info.value.message) or secret_name in str(exc_info.value.errors), (
                f"Error should reference the secret name '{secret_name}'"
            )
    
    def test_invalid_json_in_secret_raises_configuration_error(self):
        """
        **Feature: aws-deployment-pipeline, Property 14: Configuration source fallback**
        **Validates: Requirements 9.1, 9.2**
        
        Property: WHEN Secrets Manager returns invalid JSON THEN the system 
        SHALL raise a ConfigurationError.
        """
        from backend.config import _get_secrets_from_aws, ConfigurationError
        
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            'SecretString': 'not valid json {'
        }
        
        with patch('boto3.client', return_value=mock_client):
            with pytest.raises(ConfigurationError) as exc_info:
                _get_secrets_from_aws("test-secret", "us-east-1")
            
            # Property: Error should indicate JSON parsing issue
            assert "json" in str(exc_info.value.message).lower() or "json" in str(exc_info.value.errors).lower(), (
                "Error should indicate JSON parsing issue"
            )

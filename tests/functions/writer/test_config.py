import pytest
from pathlib import Path
from src.functions.writer.config import WriterConfig
from src.functions.writer.exceptions import ConfigurationError, PathValidationError
from src.functions.writer.constants import *
import os

class TestWriterConfig:
    """Test suite for WriterConfig class."""
    
    @pytest.fixture
    def tmp_config(self, tmp_path):
        """Fixture providing a temporary directory configuration."""
        return {
            "temp_dir": tmp_path / "temp",
            "drafts_dir": tmp_path / "drafts",
            "finalized_dir": tmp_path / "finalized",
            "max_file_size": DEFAULT_MAX_FILE_SIZE,
            "allowed_extensions": ALLOWED_EXTENSIONS.copy()
        }

    def test_dynamic_constraints(self, tmp_config):
        """Test dynamic constraint validation."""
        config = WriterConfig(
            temp_dir=tmp_config["temp_dir"],
            max_file_size=lambda: get_system_min_file_size() * 2
        )
        assert config.max_file_size > get_system_min_file_size()
        
        # Test invalid dynamic constraint
        with pytest.raises(ConfigurationError, match="Failed to evaluate dynamic constraint"):
            WriterConfig(
                temp_dir=tmp_config["temp_dir"],
                max_file_size=lambda: 1/0  # Will raise ZeroDivisionError
            )

    def test_constraint_resolution(self, tmp_config):
        """Test constraint resolution and validation."""
        # Test valid constraints
        config = WriterConfig(
            **tmp_config,
            max_file_size=lambda: get_available_disk_space() // 4
        )
        assert config.max_file_size <= get_available_disk_space()
        
        # Test invalid value against resolved constraint
        with pytest.raises(ConfigurationError, match="Value.*is too large"):
            WriterConfig(
                **tmp_config,
                max_file_size=get_available_disk_space() * 2
            )

    def test_field_serialization(self, tmp_config):
        """Test field serialization methods."""
        config = WriterConfig(**tmp_config)
        
        # Test to_dict
        config_dict = config.to_dict()
        assert isinstance(config_dict["temp_dir"], str)
        assert isinstance(config_dict["allowed_extensions"], list)
        
        # Test get_default_config
        defaults = WriterConfig.get_default_config()
        assert isinstance(defaults, dict)
        assert "temp_dir" in defaults
        assert isinstance(defaults["allowed_extensions"], list)

    def test_field_info(self, tmp_config):
        """Test field information retrieval."""
        config = WriterConfig(**tmp_config)
        
        # Test valid field info
        info = config.get_field_info("max_file_size")
        assert info[FIELD_INFO_TYPE] == int
        assert FIELD_INFO_HELP in info
        assert FIELD_INFO_CONSTRAINTS in info
        
        # Test invalid field
        with pytest.raises(ValueError, match="Unknown field"):
            config.get_field_info("nonexistent_field")

    @pytest.mark.parametrize("field,value,error_pattern", [
        ("max_file_size", -1, "Value.*is too small"),
        ("max_file_size", "invalid", "Invalid type"),
        ("allowed_extensions", [".invalid"], "Invalid value"),
        ("temp_dir", None, "Required field"),
    ])
    def test_field_validation(self, tmp_config, field, value, error_pattern):
        """Test field validation with various invalid values."""
        test_config = tmp_config.copy()
        test_config[field] = value
        
        with pytest.raises(ConfigurationError, match=error_pattern):
            WriterConfig(**test_config)

    def test_path_handling(self, tmp_config):
        """Test path handling and validation."""
        config = WriterConfig(**tmp_config)
        
        # Test path creation
        assert config.temp_dir.exists()
        assert config.temp_dir.is_dir()
        
        # Test path conversion
        str_config = tmp_config.copy()
        str_config["temp_dir"] = str(tmp_config["temp_dir"])
        config = WriterConfig(**str_config)
        assert isinstance(config.temp_dir, Path)
        
        # Test path validation
        invalid_path = tmp_config["temp_dir"] / "file.txt"
        invalid_path.parent.mkdir(exist_ok=True)
        invalid_path.touch()
        
        with pytest.raises(PathValidationError):
            WriterConfig(temp_dir=invalid_path)

    def test_string_representation(self, tmp_config):
        """Test string representation of configuration."""
        config = WriterConfig(**tmp_config)
        str_repr = str(config)
        
        assert CONFIG_HEADER in str_repr
        assert str(tmp_config["temp_dir"]) in str_repr
        assert str(tmp_config["max_file_size"]) in str_repr
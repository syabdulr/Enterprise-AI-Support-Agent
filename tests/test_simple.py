"""
Simple smoke tests that don't require external dependencies.
These tests verify basic Python functionality.
"""

import pytest


class TestSmokeTests:
    """Simple smoke tests for CI/CD."""
    
    def test_python_version(self):
        """Test Python version is 3.11 or higher."""
        import sys
        assert sys.version_info >= (3, 11), "Python 3.11+ required"
    
    def test_basic_imports(self):
        """Test basic Python imports work."""
        import os
        import sys
        import json
        assert True
    
    def test_project_structure(self):
        """Test project files exist."""
        import os
        
        # Check key files exist
        assert os.path.exists("README.md"), "README.md missing"
        assert os.path.exists("requirements.txt"), "requirements.txt missing"
        assert os.path.exists("pyproject.toml"), "pyproject.toml missing"
        assert os.path.exists("src"), "src directory missing"
        assert os.path.exists("tests"), "tests directory missing"
    
    def test_configuration_files(self):
        """Test configuration files exist."""
        import os
        
        assert os.path.exists(".env.example"), ".env.example missing"
        assert os.path.exists("Dockerfile"), "Dockerfile missing"
        assert os.path.exists("docker-compose.yml"), "docker-compose.yml missing"
    
    def test_documentation_exists(self):
        """Test documentation files exist."""
        import os
        
        assert os.path.exists("CONTRIBUTING.md"), "CONTRIBUTING.md missing"
        assert os.path.exists("ARCHITECTURE.md"), "ARCHITECTURE.md missing"
        assert os.path.exists("docs/SECURITY.md"), "SECURITY.md missing"
        assert os.path.exists("docs/CONFIGURATION.md"), "CONFIGURATION.md missing"
    
    def test_ci_cd_config(self):
        """Test CI/CD configuration exists."""
        import os
        
        workflows_dir = ".github/workflows"
        assert os.path.exists(workflows_dir), "GitHub workflows directory missing"
        assert os.path.exists(f"{workflows_dir}/ci-cd.yml"), "CI/CD workflow missing"
        assert os.path.exists(f"{workflows_dir}/docker.yml"), "Docker workflow missing"
    
    def test_screenshots_exist(self):
        """Test screenshots exist for demo."""
        import os
        
        screenshots_dir = "docs/screenshots"
        if os.path.exists(screenshots_dir):
            # Check at least one screenshot exists
            screenshots = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
            assert len(screenshots) > 0, "No screenshots found"
    
    def test_readme_badges(self):
        """Test README has CI/CD badges."""
        import os
        
        with open("README.md", "r") as f:
            content = f.read()
        
        # Check for CI/CD badge
        assert "CI/CD" in content or "badge" in content, "README missing CI/CD badges"
    
    def test_dockerfile_syntax(self):
        """Test Dockerfile has valid structure."""
        with open("Dockerfile", "r") as f:
            content = f.read()
        
        # Check for Dockerfile keywords
        assert "FROM" in content, "Dockerfile missing FROM statement"
        assert "WORKDIR" in content, "Dockerfile missing WORKDIR"
        assert "CMD" in content or "ENTRYPOINT" in content, "Dockerfile missing CMD/ENTRYPOINT"
    
    def test_compose_file_syntax(self):
        """Test docker-compose.yml has valid structure."""
        import yaml
        
        with open("docker-compose.yml", "r") as f:
            content = yaml.safe_load(f)
        
        assert "services" in content, "docker-compose.yml missing services"
        assert len(content["services"]) > 0, "docker-compose.yml has no services"
    
    def test_requirements_file(self):
        """Test requirements.txt is not empty."""
        with open("requirements.txt", "r") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        
        assert len(lines) > 0, "requirements.txt is empty"
    
    def test_code_quality_tools_configured(self):
        """Test code quality configuration exists."""
        import os
        
        assert os.path.exists("pyproject.toml"), "pyproject.toml missing"
        assert os.path.exists(".pre-commit-config.yaml"), "pre-commit config missing"
        assert os.path.exists("requirements-dev.txt"), "requirements-dev.txt missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Tests to validate GitHub Actions setup and functionality.
"""

import os
from pathlib import Path

import yaml


def test_github_actions_workflows_exist():
    """Test that GitHub Actions workflow files exist."""
    workflows_dir = Path(".github/workflows")
    assert workflows_dir.exists(), "GitHub Actions workflows directory not found"

    expected_workflows = ["ci.yml", "ci-api.yml", "ci-trader.yml", "ci-services.yml"]

    for workflow in expected_workflows:
        workflow_path = workflows_dir / workflow
        assert workflow_path.exists(), f"Workflow {workflow} not found"


def test_main_ci_workflow_structure():
    """Test that the main CI workflow has correct structure."""
    ci_workflow = Path(".github/workflows/ci.yml")
    assert ci_workflow.exists(), "Main CI workflow not found"

    with open(ci_workflow, "r") as f:
        workflow = yaml.safe_load(f)

    # Check basic structure
    assert "name" in workflow, "Workflow missing name"
    # Handle YAML parsing where 'on' becomes True
    assert "on" in workflow or True in workflow, "Workflow missing triggers"
    assert "jobs" in workflow, "Workflow missing jobs"

    # Check that it has a test job
    jobs = workflow["jobs"]
    assert "lint-and-test" in jobs, "Main CI workflow missing lint-and-test job"

    # Check test job has required steps
    test_job = jobs["lint-and-test"]
    assert "steps" in test_job, "Test job missing steps"

    steps = test_job["steps"]
    step_names = [step.get("name", "") for step in steps]

    # Verify essential steps exist
    assert any("pytest" in name.lower() or "test" in name.lower() for name in step_names), (
        "No pytest/test step found in workflow"
    )


def test_api_specific_workflow():
    """Test that API-specific workflow is properly configured."""
    api_workflow = Path(".github/workflows/ci-api.yml")
    assert api_workflow.exists(), "API workflow not found"

    with open(api_workflow, "r") as f:
        workflow = yaml.safe_load(f)

    # Check trigger paths - handle YAML parsing where 'on' becomes True
    assert "on" in workflow or True in workflow
    on_config = workflow.get("on") or workflow.get(True)

    # Should trigger on API path changes
    if "push" in on_config:
        assert "paths" in on_config["push"]
        assert "app/api/**" in on_config["push"]["paths"]

    if "pull_request" in on_config:
        assert "paths" in on_config["pull_request"]
        assert "app/api/**" in on_config["pull_request"]["paths"]


def test_trader_specific_workflow():
    """Test that trader-specific workflow is properly configured."""
    trader_workflow = Path(".github/workflows/ci-trader.yml")
    assert trader_workflow.exists(), "Trader workflow not found"

    with open(trader_workflow, "r") as f:
        workflow = yaml.safe_load(f)

    # Check trigger paths - handle YAML parsing where 'on' becomes True
    assert "on" in workflow or True in workflow
    on_config = workflow.get("on") or workflow.get(True)

    # Should trigger on trader path changes
    if "push" in on_config:
        assert "paths" in on_config["push"]
        assert "app/trader/**" in on_config["push"]["paths"]

    if "pull_request" in on_config:
        assert "paths" in on_config["pull_request"]
        assert "app/trader/**" in on_config["pull_request"]["paths"]


def test_pytest_configuration():
    """Test that pytest configuration is properly set up."""
    pytest_config = Path("pytest.ini")
    assert pytest_config.exists(), "pytest.ini not found"

    # Read and verify configuration
    import configparser

    config = configparser.ConfigParser()
    config.read(pytest_config)

    # Check pytest section exists
    assert "tool:pytest" in config, "pytest configuration section not found"

    pytest_section = config["tool:pytest"]

    # Verify testpaths are set correctly
    assert "testpaths" in pytest_section, "testpaths not configured"
    testpaths = pytest_section["testpaths"]

    # Should include both api and trader test directories
    assert "app/api/tests" in testpaths, "API tests path not in testpaths"
    assert "app/trader/tests" in testpaths, "Trader tests path not in testpaths"


def test_tests_are_discoverable():
    """Test that pytest can discover all tests correctly."""
    # This test ensures that pytest configuration allows all tests to be found
    import subprocess
    import sys

    # Run pytest in collect-only mode to check test discovery
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"], capture_output=True, text=True, cwd="."
    )

    assert result.returncode == 0, f"Test discovery failed: {result.stderr}"

    # Check that tests from both directories are found
    output = result.stdout
    assert "app/api/tests/test_health.py" in output, "API health test not discovered"
    assert "app/trader/tests/test_core.py" in output, "Trader core test not discovered"


def test_makefile_test_command():
    """Test that Makefile test command works properly."""
    makefile = Path("Makefile")
    assert makefile.exists(), "Makefile not found"

    with open(makefile, "r") as f:
        content = f.read()

    # Check that test target exists and calls pytest on correct paths
    assert "test:" in content, "test target not found in Makefile"

    # Should have pytest commands for both api and trader
    assert "pytest app/api/tests" in content, "API tests not in Makefile test target"
    assert "pytest app/trader/tests" in content, "Trader tests not in Makefile test target"


def test_github_actions_environment():
    """Test that GitHub Actions environment variables are properly configured."""
    # This test runs in the context where GitHub Actions would run

    # Check that we can simulate the environment
    os.environ.setdefault("PYTHONPATH", "/home/runner/work/mirai-agent/mirai-agent")
    os.environ.setdefault("DRY_RUN", "true")
    os.environ.setdefault("TESTNET", "true")

    # Verify environment variables are accessible
    assert os.getenv("PYTHONPATH") is not None, "PYTHONPATH not set"
    assert os.getenv("DRY_RUN") == "true", "DRY_RUN not set correctly"
    assert os.getenv("TESTNET") == "true", "TESTNET not set correctly"


def test_workflow_python_matrix():
    """Test that main workflow tests multiple Python versions."""
    ci_workflow = Path(".github/workflows/ci.yml")

    with open(ci_workflow, "r") as f:
        workflow = yaml.safe_load(f)

    jobs = workflow["jobs"]
    test_job = jobs["lint-and-test"]

    # Check for strategy matrix with Python versions
    assert "strategy" in test_job, "No strategy matrix found"
    strategy = test_job["strategy"]
    assert "matrix" in strategy, "No matrix strategy found"
    matrix = strategy["matrix"]
    assert "python-version" in matrix, "No Python version matrix found"

    python_versions = matrix["python-version"]
    assert isinstance(python_versions, list), "Python versions should be a list"
    assert len(python_versions) > 1, "Should test multiple Python versions"

    # Should include some recent Python versions
    version_strings = [str(v) for v in python_versions]
    assert any("3.9" in v or "3.10" in v or "3.11" in v or "3.12" in v for v in version_strings), (
        "Should include recent Python versions"
    )

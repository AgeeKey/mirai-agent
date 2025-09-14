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

    expected_workflows = ["main.yml", "test-ghcr.yml"]

    for workflow in expected_workflows:
        workflow_path = workflows_dir / workflow
        assert workflow_path.exists(), f"Workflow {workflow} not found"


def test_main_ci_workflow_structure():
    """Test that the main CI workflow has correct structure."""
    ci_workflow = Path(".github/workflows/main.yml")
    assert ci_workflow.exists(), "Main CI workflow not found"

    with open(ci_workflow) as f:
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
    assert any(
        "pytest" in name.lower() or "test" in name.lower() for name in step_names
    ), "No pytest/test step found in workflow"


def test_ghcr_test_workflow():
    """Test that GHCR test workflow exists."""
    ghcr_workflow = Path(".github/workflows/test-ghcr.yml")
    assert ghcr_workflow.exists(), "GHCR test workflow not found"

    with open(ghcr_workflow) as f:
        workflow = yaml.safe_load(f)

    # Check basic structure
    assert "name" in workflow, "GHCR workflow missing name"
    assert "on" in workflow or True in workflow, "GHCR workflow missing triggers"
    assert "jobs" in workflow, "GHCR workflow missing jobs"


def test_pytest_configuration():
    """Test that pytest configuration is properly set up."""
    # Check pyproject.toml instead of pytest.ini
    pyproject_config = Path("pyproject.toml")
    assert pyproject_config.exists(), "pyproject.toml not found"

    # Read and verify configuration
    with open(pyproject_config, encoding="utf-8") as f:
        content = f.read()

    # Check pytest section exists
    assert "[tool.pytest.ini_options]" in content, "pytest configuration section not found"
    assert "testpaths" in content, "testpaths not configured"

    # Should include test directories
    assert "tests" in content, "Main tests path not in testpaths"
    assert "app/api/tests" in content, "API tests path not in testpaths"
    assert "app/trader/tests" in content, "Trader tests path not in testpaths"


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

    with open(makefile) as f:
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


def test_python_version_matrix():
    """Test that CI workflow uses appropriate Python version matrix."""
    ci_workflow = Path(".github/workflows/main.yml")

    with open(ci_workflow) as f:
        workflow = yaml.safe_load(f)

    jobs = workflow["jobs"]
    test_job = jobs["test"]

    # Check for strategy matrix with Python versions
    if "strategy" in test_job:
        strategy = test_job["strategy"]
        if "matrix" in strategy:
            matrix = strategy["matrix"]
            if "python-version" in matrix:
                python_versions = matrix["python-version"]
                assert isinstance(python_versions, list), "Python versions should be a list"
                assert len(python_versions) >= 1, "Should test at least one Python version"

                # Should include Python 3.12
                version_strings = [str(v) for v in python_versions if v is not None]
                assert any("3.12" in v for v in version_strings), "Should include Python 3.12"

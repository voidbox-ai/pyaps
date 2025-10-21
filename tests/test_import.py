"""Basic import tests to verify package structure."""


def test_import_pyaps():
    """Test that the main package can be imported."""
    import pyaps
    assert pyaps is not None


def test_import_auth():
    """Test that the auth module can be imported."""
    from pyaps import auth
    assert auth is not None


def test_import_datamanagement():
    """Test that the datamanagement module can be imported."""
    from pyaps import datamanagement
    assert datamanagement is not None


def test_import_automation():
    """Test that the automation module can be imported."""
    from pyaps import automation
    assert automation is not None

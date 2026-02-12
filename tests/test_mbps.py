import mbps


def test_version():
    assert mbps.__version__


def test_imports():
    from mbps.core import Speedtest
    from mbps.results import SpeedtestResults
    from mbps.exceptions import SpeedtestException

    assert Speedtest
    assert SpeedtestResults
    assert SpeedtestException

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="PyATE",
    description="Python Autmoated Test Environment",
    authon="Kyle Hershberger",
    version="0.1.1",
    packages=["pyate"],
    install_requires=["matplotlib", "numpy", "pandas", "pyqt5", "pyvisa", "pyserial" "scipy"],
)

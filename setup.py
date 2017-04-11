try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name = 'PATE',
      description = 'Python Autmoated Test Environment',
      authon = 'Kyle Hershberger',
      version = '0.1.0',
      packages = ['pate'],
      install_requires = [
          'pyvisa',
          'pandas',
          'matplotlib',
          'pyqt5'
          ]
      )

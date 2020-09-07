from setuptools import setup

"""
Primer:
      pip install -e .  # from package root, install via symlinks (one-time)
      # change version here
      python setup.py sdist  # create versioned dist/*.tar.gz
      python3 -m twine upload dist/*  # choose the newest
"""

setup(name='johanna',
      version='0.4.0',
      description='Sweet tiny app framework for Jenkins driven background apps',
      url='https://github.com/turkishmaid/johanna',
      author='Sara Ziner',
      author_email='turkishmaid@example.com', # :P
      license='MIT',
      packages=['johanna'],
      install_requires=[
            'requests',
            'docopt'
      ],
      classifiers=[
            'Development Status :: 3 - Alpha',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Intended Audience :: Developers',
            'Topic :: Utilities',
      ],
      zip_safe=False)
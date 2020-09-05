from setuptools import setup

setup(name='johanna',
      version='v0.1.0',
      description='Sweet tiny app framework for Jenkins driven background apps',
      url='https://github.com/turkishmaid/johanna',
      author='Sara Ziner',
      author_email='turkishmaid@example.com',
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
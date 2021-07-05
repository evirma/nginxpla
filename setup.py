from setuptools import setup

from nginxpla import __version__

setup(
    name='nginxpla',
    version=__version__,
    description='Small and powerful real-time python nginx access log parser and analyzer with top-like style support',
    long_description=open('README.rst').read(),
    license='MIT',
    url='https://github.com/evirma/nginxpla',
    author='Eugene Myazin',
    author_email='eugene.myazin@gmail.com',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
    keywords='cli monitoring nginx log access_log system',
    packages=["nginxpla", "nginxpla/module"],
    install_requires=[
        'docopt',
        'tabulate',
        'pyyaml',
        'geoip2',
        'pyparsing',
        'crawlerdetect',
        'ua-parser',
        'user-agents',
        'tqdm'
    ],
    package_data={
        "nginxpla": ["config/*", "config/module/you_name/*"]
    },
    entry_points={
        'console_scripts': [
            'nginxpla = nginxpla.__main__:main',
        ],
    },
)

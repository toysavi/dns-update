from setuptools import setup

setup(
    name="dns_updater",
    version="1.0",
    description="DNS Updater App with PyQt5",
    author="Your Name",
    author_email="your.email@example.com",
    packages=['src'],
    install_requires=[
        'pyqt5==5.15.4',
        'pyinstaller==5.0.1',
        'pandas==1.4.3'
    ],
    entry_points={
        'console_scripts': [
            'dns_updater = src.dns_updater_gui:main'
        ]
    }
)

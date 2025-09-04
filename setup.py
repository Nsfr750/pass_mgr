from setuptools import setup, find_packages

setup(
    name="password_manager",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PySide6>=6.5.0",
        "cryptography>=41.0.0",
        "pywin32>=306; sys_platform == 'win32'",
        "pycryptodome>=3.18.0",
        "keyring>=24.0.0",
        "python-dotenv>=1.0.0"
    ],
    python_requires=">=3.9",
    entry_points={
        'console_scripts': [
            'password-manager=main:main',
        ],
    },
)

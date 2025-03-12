from setuptools import setup, find_packages

setup(
    name="pyazul",
    version="1.0.0",
    packages=find_packages(include=['pyazul', 'pyazul.*']),
    package_data={
        'pyazul': ['*', '**/*'],
    },
    include_package_data=True,
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0"
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0"
        ],
        "examples": [
            "fastapi>=0.68.0",
            "python-multipart>=0.0.5",
            "jinja2>=3.0.0",
            "uvicorn>=0.15.0"
        ]
    }
)

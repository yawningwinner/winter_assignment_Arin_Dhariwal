from setuptools import setup, find_packages

setup(
    name="merchant_api",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "sqlalchemy",
        "psycopg2-binary",
        "uvicorn",
    ]
) 
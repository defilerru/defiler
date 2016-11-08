from setuptools import setup

setup(
    name="defiler",
    version="0.0.1-dev",
    packages=["defiler"],
    include_package_data=True,
    install_requires=["aiohttp", "aiomysql"]
)

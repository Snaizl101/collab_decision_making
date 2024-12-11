from setuptools import setup, find_packages

setup(
    name="collab_decision_making",
    version="0.1",
    packages=find_packages(where="src"),  # This is important - tell it to look in src
    package_dir={"": "src"},  # This tells setuptools packages are under src
    install_requires=[
        'click',
    ],
    entry_points={
        'console_scripts': [
            'collab-decision=presentation.cli.cli:cli',  # Updated entry point
        ],
    },
)
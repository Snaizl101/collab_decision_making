from setuptools import setup, find_packages

setup(
    name="collab_decision_making",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'cli=src.presentation.cli.cli:cli'
        ],
    }
)
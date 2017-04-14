from setuptools import setup

try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
except (IOError, ImportError):
    long_description = ''


setup(
    name='role',
    author='Randy Lai',
    version='0.0.3',
    url='https://github.com/randy3k/role',
    description='R REPL build on top of prompt_toolkit',
    long_description=long_description,
    packages=["role"],
    install_requires=[
        'zmq>=13',
        'prompt_toolkit>=1.0.14,<2.0.0',
        'pygments',
    ],
    entry_points={
        'console_scripts': [
            'role = role:application.run'
        ]
    }
)

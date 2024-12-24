from setuptools import find_packages,setup

# Function to read requirements.txt
def read_requirements():
    with open("requirements.txt") as req:
        return req.read().splitlines()


setup(
    name='mcqgenarator',
    version='0.0.1',
    author='babasahebpinjar',
    author_email='babasahebpinjar@gmail.com',
    install_requires=read_requirements(),
    packages=find_packages()
)
 
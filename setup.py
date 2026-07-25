from setuptools import setup,find_packages
from typing import List
def get_requirements()->List[str]:
    requirement_lst:List[str]=[]
    try:
        with open("requirements.txt","r") as file:
            lines=file.readlines()

            for line in lines:
                requirement=line.strip()
                if requirement != '-e .':
                    requirement_lst.append(requirement)
    except FileNotFoundError:
        print("requirements.txt file not found")
    return requirement_lst


setup(
    name="NetworkSecurity",
    version="0.0.1",
    author="Sourav",
    author_email="lcs.souravkrsahu@Gmail.com",
    packages=find_packages(),
    install_requires=get_requirements()
)
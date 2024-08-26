from setuptools import setup, find_packages
def get_requirements(path: str):
    return [l.strip() for l in open(path)]

setup(
    name='futureagi',
    version='0.2.1',
    author='Future AGI',
    author_email='noreply@mail.futureagi.com',
    description='Empowering GenAI teams to maintain peak model accuracy in production environments.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/future-agi/client',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=get_requirements("requirements.txt"),
)
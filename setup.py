from setuptools import setup, find_packages
def get_requirements(path: str):
    return [l.strip() for l in open(path)]

setup(
    name='fi-tcs',
    version='0.1.1',
    author='FutureAgi',
    author_email='noreply@mail.futureagi.com',
    description='We help GenAI teams maintain high-accuracy for their Models in production.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/future-agi/clients',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=get_requirements("requirements.txt"),
)

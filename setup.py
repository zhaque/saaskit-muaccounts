from setuptools import setup, find_packages

install_requires = [
        'setuptools',
        'Django',
        'PIL==1.1.6',
]

setup(name="saaskit-muaccounts",
        version="0.1.2",
        description="Domain-based multi-user accounts",
        author="SaaSkit",
        author_email="admin@saaskit.org",
        packages=find_packages(),
        include_package_data=True,
        install_requires = install_requires,
        entry_points="""
        # -*- Entry points: -*-
        """,
        dependency_links = ['http://dist.repoze.org',],
)

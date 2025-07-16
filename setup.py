from setuptools import setup, find_packages

setup(
    name="AI4RM",
    version="0.1.0",
    description="의료데이터 가명화·활용 플랫폼",
    author="BenKorea",
    author_email="benkorea.ai@gmail.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "typer>=0.9",
        # 여기에 추가 패키지 기입
    ],
    extras_require={
        "dev": ["pytest", "black", "isort"],
    },
)

import os
import subprocess

PYENV_VERSION_FILE = "python-version"

# python-version 파일 읽기
def read_python_version(file_path):
    if not os.path.exists(file_path):
        print(f"[ERROR] {file_path} 파일이 존재하지 않습니다.")
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        version = f.read().strip()
    return version

def set_pyenv_local(version):
    try:
        subprocess.run(["pyenv", "local", version], check=True)
        print(f"[INFO] pyenv local 버전이 {version}으로 설정되었습니다.")
    except subprocess.CalledProcessError:
        print(f"[ERROR] pyenv local {version} 설정 실패. 해당 버전이 설치되어 있는지 확인하세요.")

def main():
    version = read_python_version(PYENV_VERSION_FILE)
    if version:
        set_pyenv_local(version)

if __name__ == "__main__":
    main()

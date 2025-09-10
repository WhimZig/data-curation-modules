import os
import subprocess
import sys
from pathlib import Path


def run_commands_in_dirs_with_pyproject(
    root_dir: str = ".",
    commands: list[str] = [],
) -> int:
    """Run a list of commands in all directories with a `pyproject.toml` file.

    Args:
        root_dir (str, optional): The root directory to start the search from. Defaults to ".".
        commands (list[str], optional): The list of commands to run. Defaults to [].

    Returns:
        int: The lowest error code of any of the executed commands, above 0.
    """
    # Get the absolute path of the root directory
    root_path = Path(root_dir).resolve()

    exit_code = 0
    # Walk through the directories at the top level of the root directory
    for dir_path in root_path.iterdir():
        if dir_path.is_dir() and (dir_path / "pyproject.toml").is_file():
            print(f"\n\nProcessing {dir_path}")

            # Change to the directory
            os.chdir(dir_path)

            try:
                # Run each command
                for command in commands:
                    print(f"Running: {command}")
                    subprocess.run(command, shell=True, check=True, text=True)

            except subprocess.CalledProcessError as e:
                print(
                    f"\nError with return code {e.returncode} "
                    f"running command: {e.cmd}"
                )
                if exit_code == 0:
                    exit_code = e.returncode
                else:
                    exit_code = min(exit_code, e.returncode)
            finally:
                # Change back to the root directory
                os.chdir(root_dir)
    return exit_code


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_commands_for_all_modules.py <command1> <command2> ...")
        sys.exit(1)

    commands = sys.argv[1:]
    exit_code = run_commands_in_dirs_with_pyproject(commands=commands)
    sys.exit(exit_code)

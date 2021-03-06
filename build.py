"""
Generate shell scripts and crontab for deployment.
"""
import os
import pdb
import yaml
import sys

with open("./config/docker.yml", "r") as fin:
    config_docker = yaml.load(fin)

with open("./config/scripts.yml", "r") as fin:
    config_scripts = yaml.load(fin)


def check_version():
    """
    Check system python version and raise exception if <2.7
    """
    if sys.version_info[0] < 2:
        raise Exception("Python v2.7+ is required")

    elif sys.version_info[0] == 2 and sys.version_info[1] < 7:
        raise Exception("Python v2.7+ is required")

    return


def get_docker_cmd(options, image, command, args):
    options = "" if not options else " ".join(options)
    args = "" if not args else " ".join(args)
    return "docker run {} {} {} {}".format(options, image, command, args)


def get_shell_script(build_path, filename, path, script_name, docker_cmd):
    header = "#!/usr/bin/env bash \n"

    cmd = filename + " " + script_name

    return (
        docker_cmd.replace("$BUILD_PATH", build_path)
        .replace("$WORKDIR", path)
        .replace("$CMD", cmd)
    )


def cron_entry(cron, path):
    return "{} bash {}".format(cron, path)


def list_to_file(filename, list_, write_mode="a", header=None):
    with open(filename, write_mode) as fout:
        if header:
            fout.write(header)

        for l in list_:
            fout.write(l)
            fout.write("\n")

    return


if __name__ == "__main__":
    check_version()

    CRON_FILENAME = "crontab.sh"

    CRON_HEADER = """# Crontab entries generated by python-docker-cron\n"""

    LAUNCHER_FILENAME = "launch.py"

    cwd = os.getcwd()

    # the parent directory of this file, and the presumed
    # location of launcher.py, which will be set as the docker
    # working directory (workdir)
    current_dir = os.path.basename(cwd)

    parent_path = os.path.dirname(os.getcwd())

    crons = []

    for script_name in config_scripts.keys():

        script = config_scripts.get(script_name)

        if not script.get("enabled"):
            continue

        docker_name = script.setdefault("docker_cmd", "default")

        docker_cfg = config_docker.get(docker_name)

        docker_cmd = get_docker_cmd(
            docker_cfg.get("options"),
            docker_cfg["image"],
            docker_cfg.get("command"),
            docker_cfg.get("args"),
        )

        sh = get_shell_script(
            parent_path, LAUNCHER_FILENAME, current_dir, script_name, docker_cmd
        )

        sh_filename = "{}/scripts/{}.sh".format(cwd, script_name)

        list_to_file(sh_filename, [], header=sh, write_mode="w")

        cron = cron_entry(script["cron"], sh_filename)

        crons.append(cron)

    list_to_file(CRON_FILENAME, crons, header=CRON_HEADER, write_mode="w")

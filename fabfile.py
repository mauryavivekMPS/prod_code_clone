__author__ = 'johnm'

from fabric.api import run, cd, env, prefix

env.use_ssh_config = True
env.warn_only = True

env.roledefs = {
    'prod': ['impactvizor_prod01'],
    'qa': ['impactvizor_qa01']
}


def ivetl_conf():
    if env.host_string in env.roledefs['prod']:
        return "source /opt/highwire/impactvizor-pipeline/conf/prod.sh"
    elif env.host_string in env.roledefs['qa']:
        return "source /opt/highwire/impactvizor-pipeline/conf/qa.sh"

venv_prefix = "source /opt/highwire/virtualenv/impactvizor-pipeline/bin/activate"


#
# Stopping and starting
#

def stop_celery():
    pass


def start_celery():
    pass


def restart_celery():
    pass


def stop_rabbitmq():
    pass


def start_rabbitmq():
    pass


def restart_rabbitmq():
    pass


def restart_ivetl():
    restart_rabbitmq()
    restart_celery()


#
# Updating
#

def update_pip():
    with prefix(ivetl_conf()):
        with prefix(venv_prefix):
            with cd("/opt/highwire/impactvizor-pipeline"):
                run("pip install -r requirements.txt")


def git_pull():
    with cd("/opt/highwire/impactvizor-pipeline"):
        run("git pull")


def update_ivetl():
    git_pull()
    update_pip()
    restart_ivetl()


#
# Investigative tasks
#

def git_status():
    with cd("/opt/highwire/impactvizor-pipeline"):
        run("git status")
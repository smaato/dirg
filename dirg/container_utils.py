from __future__ import print_function
from docker.utils import kwargs_from_env
import sys
import docker
import json


def find_docker_host(cli, name, conf):
    new_cli = cli
    if conf.get('docker_host'):
        args = kwargs_from_env(assert_hostname=False)
        args['base_url'] = conf.get('docker_host')
        args['version'] = '1.17'
        return docker.Client(**args)    

    if not new_cli:
        print('DOCKER_HOST not set globally or for container %s' % name)
        sys.exit(-1)

    return new_cli


def create_container(cli, name, conf):
    host = find_docker_host(cli, name, conf)
    sys.stdout.flush()
    try:
        host.create_container(name=name, image=conf.get('image'),
                              hostname=name, ports=conf.get('ports'),
                              environment=conf.get('env'),
                              volumes=conf.get('volumes'),
                              command=conf.get('command', ''))
    except docker.errors.APIError as e:
        print(e)
        sys.exit(-1)
    

def pull_container(cli, name, conf):
    print('Pulling image %s ... ' % conf.get('image'))
    cli = find_docker_host(cli, name, conf)
    sys.stdout.flush()
    try:
        for line in cli.pull(conf.get('image'), stream=True):
            print(json.dumps(json.loads(line), indent=4))
    except docker.errors.APIError as e:
        print(e)
        sys.exit(-1)


def start_container(cli, name, conf):
    print('Starting container %s ... ' % name, end='')
    host = find_docker_host(cli, name, conf)
    sys.stdout.flush()
    try:
        host.start(
            container=name, port_bindings=conf.get('port_bindings'),
            binds=conf.get('volume_bindings'), links=conf.get('links'),
            network_mode=conf.get('net', 'bridge'))
    except docker.errors.APIError as e:
        print(e)
        sys.exit(-1)
    print('ok')


def stop_container(cli, name, conf):
    print('Stopping container %s ... ' % name, end='')
    host = find_docker_host(cli, name, conf)  
    sys.stdout.flush()
    try:
        host.stop(container=name)
    except docker.errors.APIError as e:
        print(e)
        sys.exit(-1)
    print('ok')


def remove_container(cli, name, conf):
    print('Removing container %s ... ' % name, end='')
    cli = find_docker_host(cli, name, conf)    
    sys.stdout.flush()
    try:
        cli.stop(container=name)
        cli.remove_container(container=name, v=True)
    except docker.errors.APIError:
        print('not found')
        return
    print('ok')


def build_container(cli, name, conf):
    print('Building container %s ... ' % name)
    cli = find_docker_host(cli, name, conf)
    sys.stdout.flush()
    try:
        if 'path' in conf:
            [print(json.loads(line).get('stream', ''), end='')
             for line in cli.build(path=conf.get('path'), rm=True)]
    except docker.errors.APIError as e:
        print(e)
        sys.exit(-1)


def show_container_logs(cli, name, conf):
    print('Showing logs for container %s ... ' % name)
    cli = find_docker_host(cli, name, conf)
    try:
        [print(line, end='') for line in cli.logs(container=name, stderr=True, stdout=True, stream=True)]
    except docker.errors.APIError as e:
        print(e)
        sys.exit(-1)
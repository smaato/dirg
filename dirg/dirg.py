#!/usr/bin/env python
from __future__ import print_function
import docker
from docker.utils import kwargs_from_env
import argparse
import yaml
import ConfigParser
import os
import jinja2
import service_utils
import sys
import _version
import requests


HELP = '''
Dirg reads a yaml file describing services made of docker container definitions
and allows those to apply a number of command to these groups of containers.

The current dir needs to have a file called dirg.cfg or you need an environment
variable DIRG_CFG pointing to one. This config file contains a reference to
the service description to be used.

The DOCKER_HOST environment variable is used to determin to docker server.
'''

DIRG_CFG_FILE = 'dirg.cfg'
DIRG_CFG_ENV = 'DIRG_CFG'

# removes urllib3's InsecurePlatformWarning SSL warning when in
# use with older python version
requests.packages.urllib3.disable_warnings()

config = ConfigParser.ConfigParser()

# when using SSL:
# $ export DOCKER_HOST=https://docker.local:2376
# $ export DOCKER_CERT_PATH=/home/user/.docker/
# $ export DOCKER_TLS_VERIFY=1

if 'DOCKER_HOST' in os.environ:
    try:
        args = kwargs_from_env(assert_hostname=False)
        args['base_url'] = os.environ.get('DOCKER_HOST')
        args['version'] = '1.17'
        cli = docker.Client(**args)
    except Exception as e:
        print('Error connecting to docker host.')
        print(e)
        sys.exit(-1)
else:
    cli = None

container = {}
services = {}


def service_by_name(name):
    if name in services:
        return services[name]
    print('Invalid service %s' % name)
    sys.exit(-1)


def foreach_service(args, command):
    # check if all services exist before calling the
    # first one
    for name in args.name:
        service_by_name(name)

    for name in args.name:
        command(cli, service_by_name(name))


def run_service_cmd(args):
    foreach_service(args, service_utils.run_service)


def start_service_cmd(args):
    foreach_service(args, service_utils.start_service)


def stop_service_cmd(args):
    foreach_service(args, service_utils.stop_service)


def build_service_cmd(args):
    foreach_service(args, service_utils.build_service)


def show_service_cmd(args):
    foreach_service(args, service_utils.show_service)


def pull_service_cmd(args):
    foreach_service(args, service_utils.pull_service)


def remove_service_cmd(args):
    foreach_service(args, service_utils.remove_service)


def update_service_cmd(args):
    foreach_service(args, service_utils.update_service)


def list_services_cmd(args):
    foreach_service(args, service_utils.list_services)


def show_service_logs_cmd(args):
    foreach_service(args, service_utils.show_service_logs)


def show_service_stats_cmd(args):
    foreach_service(args, service_utils.show_service_stats)


def info_cmd(args):
    check_environment()


def print_debug(args, message):
    if args.debug:
        print(message)


def load_service_config(args):
    """loads service definition specified in config file"""
    try:
        service_file = config.get('DEFAULT', 'dirg_services', None)
    except ConfigParser.NoOptionError:
        print('Dirg config needs a key called "dirg_services".')
        sys.exit(-1)

    if not os.path.isfile(service_file):
        print('Can not read service config file: %s' % service_file)
        sys.exit(-1)

    print_debug(args, 'Reading services from %s' % service_file)

    with open(config.get('DEFAULT', 'dirg_services'), 'r') as f:
        service_content = f.read()
        service_template = jinja2.Template(service_content)
        service_yml = service_template.render(dict(config.items('DEFAULT'), env=os.environ))
        try:
            services_def, container = yaml.load_all(service_yml)
        except ValueError as e:
            print('Error reading service description %s: %s' % (service_file, e))
            sys.exit(-1)

    if services_def is not None and container is not None:
        global services
        for s in services_def:
            service_container = []
            for container_name in services_def[s]:
                if container_name not in container:
                    print('"%s" not a valid container name for service "%s"' % (container_name, s))
                    sys.exit(-1)
                service_container.append(
                    {'name': container_name,
                     'conf': container[container_name]})
            services[s] = {'name': s, 'container': service_container}


def load_config(args):
    """loads config file from local dir or from DIRG_CFG_ENV"""
    if DIRG_CFG_ENV in os.environ and os.path.isfile(DIRG_CFG_FILE):
        print_debug(args, 'Reading cfg from %s then from %s'
                    % (DIRG_CFG_FILE, os.environ[DIRG_CFG_ENV]))
        config.readfp(open(DIRG_CFG_FILE))
        config.read([os.environ[DIRG_CFG_ENV]])
    elif DIRG_CFG_ENV in os.environ and not os.path.isfile(DIRG_CFG_FILE):
        print_debug(args, 'Reading cfg from %s' % os.environ[DIRG_CFG_ENV])
        config.read([os.environ[DIRG_CFG_ENV]])
    elif os.path.isfile(DIRG_CFG_FILE):
        print_debug(args, 'Reading cfg from %s' % DIRG_CFG_FILE)
        config.readfp(open(DIRG_CFG_FILE))
    else:
        print('dirg.cfg not found and env variable %s not set.' % DIRG_CFG_ENV)
        sys.exit(-1)


def check_environment():
    print('Version %s' % _version.__version__)
    print('DIRG_CFG = %s' % os.environ.get('DIRG_CFG'))
    print('DOCKER_HOST = %s' % os.environ.get('DOCKER_HOST'))
    print('DOCKER_CERT_PATH = %s'
          % os.environ.get('DOCKER_CERT_PATH'))
    print('DOCKER_TLS_VERIFY = %s'
          % os.environ.get('DOCKER_TLS_VERIFY'))


def main():
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        'name',
        default=['all'],
        nargs='*',
        help='service name',
        action='store')
    parent_parser.add_argument(
        '-d', '--debug',
        default=False,
        dest='debug',
        help='Print debug info.',
        action='store_true')

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=HELP,
        epilog='')
    parser.add_argument(
        '-d', '--debug',
        default=False,
        dest='debug',
        help='Print debug info.',
        action='store_true')

    subparsers = parser.add_subparsers()

    parser_run = subparsers.add_parser(
        'run',
        help='Create all container and start them.',
        parents=[parent_parser])
    parser_run.set_defaults(func=run_service_cmd)

    parser_info = subparsers.add_parser(
        'info', help='Prints out environment info.')
    parser_info.set_defaults(func=info_cmd)

    parser_start = subparsers.add_parser(
        'start', help='Start all service container.', parents=[parent_parser])
    parser_start.set_defaults(func=start_service_cmd)

    parser_stop = subparsers.add_parser(
        'stop', help='Stop all service container', parents=[parent_parser])
    parser_stop.set_defaults(func=stop_service_cmd)

    parser_remove = subparsers.add_parser(
        'rm', help='Remove all service service.', parents=[parent_parser])
    parser_remove.set_defaults(func=remove_service_cmd)

    parser_build = subparsers.add_parser(
        'build',
        help='Build all service container images.',
        parents=[parent_parser])
    parser_build.set_defaults(func=build_service_cmd)

    parser_list = subparsers.add_parser(
        'ps',
        help='List all services and their container status.',
        parents=[parent_parser])
    parser_list.set_defaults(func=list_services_cmd)

    parser_show = subparsers.add_parser(
        'show', help='Show service container config.', parents=[parent_parser])
    parser_show.set_defaults(func=show_service_cmd)

    parser_pull = subparsers.add_parser(
        'pull', help='Pull service container images.', parents=[parent_parser])
    parser_pull.set_defaults(func=pull_service_cmd)

    parser_logs = subparsers.add_parser(
        'logs', help='Show service logs.', parents=[parent_parser])
    parser_logs.set_defaults(func=show_service_logs_cmd)

    parser_update = subparsers.add_parser(
        'update', help='Update service.', parents=[parent_parser])
    parser_update.set_defaults(func=update_service_cmd)

    parser_stats = subparsers.add_parser(
        'stats', help='Show service stats.', parents=[parent_parser])
    parser_stats.set_defaults(func=show_service_stats_cmd)

    args = parser.parse_args()

    if args.debug:
        check_environment()

    load_config(args)
    load_service_config(args)

    args.func(args)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

import container_utils
import yaml
from sys import stdin
import docker
import sys
import json


def run_service(cli, service):
    print('Running service ' + service['name'])
    for container in service['container']:
        container_utils.create_container(
            cli, container['name'], container['conf'])
        container_utils.start_container(
            cli, container['name'], container['conf'])


def start_service(cli, service):
    print('Starting service ' + service['name'])
    for container in service['container']:
        container_utils.start_container(
            cli, container['name'], container['conf'])


def stop_service(cli, service):
    print('Stopping service ' + service['name'])
    for container in service['container']:
        container_utils.stop_container(
            cli, container['name'], container['conf'])


def update_service(cli, service):
    print('Updating service ' + service['name'])
    for container in service['container']:
        container_utils.pull_container(
            cli, container['name'], container['conf'])
        container_utils.remove_container(
            cli, container['name'], container['conf'])
        container_utils.create_container(
            cli, container['name'], container['conf'])
        container_utils.start_container(
            cli, container['name'], container['conf'])


def build_service(cli, service):
    print('Building service ' + service['name'])
    for container in service['container']:
        container_utils.build_container(
            cli, container['name'], container['conf'])


def show_service(cli, service):
    for container in service['container']:
        print('Container %s:' % container['name'])
        print('\n' + yaml.dump(container['conf']))


def pull_service(cli, service):
    for container in service['container']:
        container_utils.pull_container(
            cli, container['name'], container['conf'])


def remove_service(cli, service):
    print('Removing service ' + service['name'])
    for container in service['container']:
        container_utils.remove_container(
            cli, container['name'], container['conf'])


def show_service_logs(cli, service):
    choice = '1'
    if len(service['container']) > 1:
        print('Choose container:')
        num = 1
        for container in service['container']:
            print('%s) %s' % (num,  container['name']))
            num += 1
        choice = stdin.readline()
    container = service['container'][int(choice) - 1]
    container_utils.show_container_logs(
        cli, container['name'], container['conf'])


def show_service_stats(cli, service):
    for container in service['container']:
        host = container_utils.find_docker_host(cli, container['name'], container['conf'])
        try:
            for stats_json in host.stats(container['name']):
                stats = json.loads(stats_json)
                #print(json.dumps(json.loads(line), indent=4))
                print(stats['cpu_stats'])
        except docker.errors.APIError as e:
            print(e)
            sys.exit(-1)



def list_services(cli, service):
    print('\n{:<25} {:<25} {:<25} {:<25}'.format('Service', 'Container', 'Status', 'Host'))
    print('-' * 120)

    for container in service['container']:
        host = container_utils.find_docker_host(cli, container['name'], container['conf'])
        container_status = host.containers()
        status = next(
            (c for c in container_status
                if '/' + container['name'] in c['Names']), None)

        if status:
            print('{:<25} {:<25} {:<25} {:<25}'.format(
                service['name'], container['name'], status['Status'], container['conf'].get('docker_host', '')))
        else:
            print('{:<25} {:<25} not available'.format(
                service['name'], container['name']))

    print(' ')

Dirg is an orchestration tool for docker. It reads a yaml file
describing services made of docker container definitions and allows to
apply a number of commands to these groups of containers.

Why another orchestration tool?
===============================

-  Support for multi-host docker setups
-  Support for templating in service description

Installation
============

Make sure you have

-  Python 2.7, 3.x is not supported yet
-  Python setuptools are installed

You can install Dirg from the Python Package Index with

::

    $ pip install dirg 

Or you can clone the repository, then

::

    $ python setup.py install

To check if the installation was successful, execute

::

    $ dirg info    

Setting the docker host
=======================

You can either set the ``DOCKER_HOST`` environment variable or set a
specific docker host per container in the service description.

Using a local docker host:

::

    $ export DOCKER_HOST=unix:///var/run/docker.sock

Using a remote docker host via HTTP:

::

    $ export DOCKER_HOST=tcp://remote.host:2375

Using a remote docker host via HTTPS:

::

    $ export DOCKER_HOST=https://remote.host:2375
    $ export DOCKER_CERT_PATH=/path/to/client/cert.pem
    $ export DOCKER_TLS_VERIFY=1

Dirg Commands
=============

Most commands have the form:

::

    $ dirg COMMAND SERVICE_NAME

If ``SERVICE_NAME`` is missing, ``all`` is the default service name.

``COMMAND`` can be

::

    run                 Create all container and start them.
    info                Prints out environment info.
    start               Start all service container.
    stop                Stop all service container
    rm                  Remove all service service.
    build               Build all service container images.
    ps                  List all services and their container status.
    show                Show service container config.
    pull                Pull service container images.
    logs                Show service logs.
    update              Update service.
    stats               Show service stats.

Adding ``-d`` will print out additional debug information. This is
valuable when you want to make sure Dirg is finding the right service
configuration. ``info`` shows all environment variables needed for a SSL
connection.

Service Configuration
=====================

To configure Dirg you need a configuration file called ``dirg.cfg`` and
a yaml description of your services. When you execute Dirg, it looks for
file named ``dirg.cfg`` in the current directory. You can set an
environment variable ``DIRG_CFG`` to point to your ``dirg.cfg`` file.

A minimal ``dirg.cfg`` looks like this:

::

    [DEFAULT]
    dirg_services = /path/to/dirg-services.yml

It holds a reference to the file describing your docker based services.
In addition, you may define your own properties and values which you can
then use in your service description. E.g. you could add you docker
image registry URL to ``dirg.cfg`` and then reference it in your
container definitions.

A ``dirg-services.yml`` looks like this:

::

    --- 
    service1:
        - container1
        - container2
    service2:
        - container3
        - container4
    all:
        - container1
        - container2
        - container3    
        - container4
        - container5
    ---

    container1:
        image:  imagename
        volumes: volumes
        volume_bindings: volume bindings
        
    container2:
        image:  imagename
        volumes: volumes
        volume_bindings: volume bindings

    ...

This yaml file contains 2 sub-documents (separated by ---). The first
document describes all existing services. The second one describes the
containers used by the services above.

If you name a service ``all`` it will be the default service used by
Dirg when you don't name a service upon calling Dirg commands.

Container Configuration
=======================

Dirg supports the following container properties (more will be added as
needed):

+--------------------+--------------------------------------------+
| Property           | Description                                |
+====================+============================================+
| image              | Image to use                               |
+--------------------+--------------------------------------------+
| docker\_host       | Docker host to run this container on       |
+--------------------+--------------------------------------------+
| net                | Network config                             |
+--------------------+--------------------------------------------+
| env                | Environment variables                      |
+--------------------+--------------------------------------------+
| volumes            | Volumes for the container                  |
+--------------------+--------------------------------------------+
| volume\_bindings   | Mapping of container volumes               |
+--------------------+--------------------------------------------+
| ports              | Ports opened by the container              |
+--------------------+--------------------------------------------+
| port\_bindings     | Mapping to host ports                      |
+--------------------+--------------------------------------------+
| links              | Docker links to other container            |
+--------------------+--------------------------------------------+
| command            | Command to execute when container starts   |
+--------------------+--------------------------------------------+

This is a commented sample container definition using every
configuration possible:

::

    # You can use comments in dirg-services.yml, block comments start with {# and end with #}
    # my_container will be set as container name on the docker host.
    my_container: 
        
        # Stay DRY by using properties defined in dirg.cfg
        # Variables are enclosed in {{property_name}}
        image: {{registry}}/my_image_name
        
        # Run each command concerning this container on the following docker host
        docker_host: https://my.docker.host:2376
        
        # Use host network instead of bridge, which is default
        net: host
        
        # Define environment variables
        env:
            ENV1: value1
            ENV2: value2
        
        # Anywhere in dirg-services.yml you can also reference properties defined
        # as environment variables in the shell Dirg is running in.
        # This fills the docker environment variable with the contents of an
        # environment variable defined in the shell. If the shell environment
        # variable is not available, 'secret' is used as a default    
        env:
            MY_PASSWORD: {{env['PASSWORD'] or 'secret'}}
        
        # Define volumes for the container
        volumes: [/logs, /data]
        
        # Then map them to host directories, specified in a property read from dirg.cfg
        volume_bindings:
            {{data_dir}}: {bind: /data}
            {{logs_dir}}: {bind: /logs}
        
        # Define ports exposed by the container
        ports: [80, 90]
        
        # Then map them to host ports
        port_bindings: {80: 8080, 90: 9090}
        
        # Ugly workaround to define a UDP port. This will be improved in a later version:
        ports:
            - !!python/tuple [8125, udp]
        port_bindings: {8125: 8125}
        
        # Link containers
        links: {db: db}

        # Execute command in container when it starts
        command: '/app/run_benchmark -p 80 -c 90'

Advanced Templating
-------------------

Since the service description is a Jinja2 template you may do everything
you can do in Jinja2. Take a look at the Jinja2 template designer
documentation at http://jinja.pocoo.org/docs/dev/templates/ .

Some ideas of what you could do:

::

    ---
    # Define a service my_service with 3 containers
    my_service: 
    {% for idx in [1, 2, 3] %}
      - container{{idx}}
    {% endfor %}
    ---

    # Define 3 container to run on 3 different docker hosts
    {% for idx in [1, 2, 3] %}
    container{{idx}}:
        image: {{registry}}/my-image
        docker_host: https://docker-host0{{idx}}
    {% endfor %}    

To check the result of your templating you can call
``dirg show my_service`` which would result in the following output:

::

    container1:
        image: my-registry:5000/my-image
        docker_host: https://docker-host01

    container2:
        image: my-registry:5000/my-image
        docker_host: https://docker-host02

    container3:
        image: my-registry:5000/my-image
        docker_host: https://docker-host03 

Or you could define certain container or services only when run in a
certain environment:

::

    # Only define this container if there is an environment variable 'dev'
    {% if env['dev'] %}
    container:
        image: my-registry:5000/my-image
    {% endif %}

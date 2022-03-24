import logging
import docker

def ready(current_configuration, output, test_id): 
    logging.debug(f"Testing if SUT is correctly deployed.")

    sut_hostname = current_configuration["docker_test_hostname"]
    # docker_client = docker.DockerClient(base_url=f"{sut_hostname}:2375")
    docker_client = docker.DockerClient(base_url=f"unix:///var/run/docker.sock")
    # docker_client = "unix:///var/run/docker.sock"
    tests = current_configuration["docker_test_if_image_is_present"].split()

    for test in tests:    
        found = False
        for container in docker_client.containers.list():            
            if test in container.name:
                found = True

        if not found:
            logging.critical(f"Could not find a container that contains '{test}' within the running containers.")
            return False

    return True
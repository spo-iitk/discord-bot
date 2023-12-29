import docker

def get_running_containers_status():
    client = docker.from_env()

    running_containers = client.containers.list(all=True)

    all_container_status = []

    for container in running_containers:
        container_id = container.short_id
        container_name = container.name
        container_status = container.status
        all_container_status.append(f"Container ID: {container_id}, Name: {container_name}, Status: {container_status}")
    
    return all_container_status

def restart_container(container_name):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        container.restart()
        return True,f"Container '{container_name}' restarted."
    except docker.errors.NotFound:
        return False,f"Container '{container_name}' not found."
    except docker.errors.APIError as e:
        return False,f"Error in restarting container '{container_name}'. Error: {e}"

# if __name__ == "__main__":
    # print(get_running_containers_status())
    # print(restart_container("ras-backend-server-1"))
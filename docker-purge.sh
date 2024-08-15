# shut down all containers (remove images and volumes)
docker compose -f docker-compose-production.yml down --volumes --rmi local
# docker-compose -f docker-compose-develop.yml down --volumes --rmi local

# make sure containers are removed (if not running)
docker container rm -f sbmlutils_nginx_1
docker container rm -f sbmlutils_backend_1
docker container rm -f sbmlutils_frontend_1

# make sure images are removed
docker image rm -f sbmlutils_nginx:latest
docker image rm -f sbmlutils_backend:latest
docker image rm -f sbmlutils_frontend:latest

# make sure volumes are removed
docker volume rm -f sbmlutils_node_modules
docker volume rm -f sbmlutils_vue_dist

# cleanup all dangling images, containers, volumes and networks
docker system prune --force

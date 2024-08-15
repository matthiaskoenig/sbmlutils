git pull
./docker-purge.sh
docker compose -f docker-compose-production.yml up --force-recreate --always-recreate-deps --build --detach

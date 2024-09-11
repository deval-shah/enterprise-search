docker-compose -f docker/docker-compose.yml down
rm -rf data/slim/uploads/*/*
docker-compose -f docker/docker-compose.yml up -d

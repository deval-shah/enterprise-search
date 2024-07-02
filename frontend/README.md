# LlamaSearch UI
- The UI is written in next.js 14
- All dependencies are handled in the docker build

## Prerequisites
- Docker

## Test Frontend using Docker
1. Build image: docker build -t llamasearch-frontend .
2. Run container: docker-compose up
3. Access at `http://localhost:3000`
4. Stop Frontend: docker-compose down

## Learn More

To learn more about Next.js, take a look at the following resources:
- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.
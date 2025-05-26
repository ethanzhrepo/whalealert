# docker run -d --name nats-server -p 4222:4222 nats

docker run -d \
  --name nats-server \
  -p 4222:4222 \
  -p 8080:8080 \
  -v $(pwd)/nats.conf:/etc/nats/nats.conf \
  nats:latest -c /etc/nats/nats.conf
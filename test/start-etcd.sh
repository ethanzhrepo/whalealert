docker run -d --name etcd \
  -p 2379:2379 -p 2380:2380 \
  --env ALLOW_NONE_AUTHENTICATION=yes \
  --env ETCD_ENABLE_V2=true \
  --env ETCD_ADVERTISE_CLIENT_URLS=http://127.0.0.1:2379 \
  --env ETCD_LISTEN_CLIENT_URLS=http://127.0.0.1:2379 \
  quay.io/coreos/etcd:latest
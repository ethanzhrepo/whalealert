#!/bin/bash

ENDPOINT=http://127.0.0.1:2379

etcdctl --endpoints=$ENDPOINT "$@"
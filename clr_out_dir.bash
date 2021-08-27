CONTAINERNAME=clearout

docker kill $CONTAINERNAME
docker rm $CONTAINERNAME
docker create --name $CONTAINERNAME -it \
  -v $(pwd)/out:/home/cdeep3m/mount/out \
  --network=host \
  --entrypoint /bin/bash \
  ncmir/cdeep3m


docker start $CONTAINERNAME
sleep 1
docker exec $CONTAINERNAME rm -r mount/out/


#docker run -it -v $(pwd):/home/cdeep3m/mount/out --entrypoint /bin/bash ncmir/cdeep3m "rm mount/out/*"

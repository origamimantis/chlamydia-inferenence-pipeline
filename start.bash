CONTAINERNAME=big

function closecontainer()
{
  docker kill $CONTAINERNAME &>/dev/null
  docker rm $CONTAINERNAME &>/dev/null
}
trap closecontainer SIGINT


if [ $1 ] && [ $2 ]
then
  echo "Clearing out the output folder"
  ./clr_out_dir.bash &>/dev/null
  echo "...done"

  echo "Removing existing containers"
  closecontainer
  echo "...done"

  echo "Creating a new container"
  docker create --name $CONTAINERNAME -it \
    -v $(pwd)/$1:/home/cdeep3m/mount/model \
    -v $(pwd)/$2:/home/cdeep3m/mount/in \
    -v $(pwd)/out:/home/cdeep3m/mount/out \
    --network=host --gpus all \
    --entrypoint /bin/bash \
    ncmir/cdeep3m
  docker start $CONTAINERNAME &>/dev/null
  docker exec $CONTAINERNAME mkdir /home/cdeep3m/mount/out/logs/
  docker exec $CONTAINERNAME touch /home/cdeep3m/mount/out/logs/prediction.log
  docker exec $CONTAINERNAME touch /home/cdeep3m/mount/out/logs/preprocessing.log
  docker exec $CONTAINERNAME touch /home/cdeep3m/mount/out/logs/postprocessing.log
  echo "...done"
  
  echo "Running prediction"
  docker exec $CONTAINERNAME tail -f \
    mount/out/logs/prediction.log \
    mount/out/logs/preprocessing.log \
    mount/out/logs/postprocessing.log &

  docker exec $CONTAINERNAME ./runprediction.sh \
    /home/cdeep3m/mount/model/ /home/cdeep3m/mount/in /home/cdeep3m/mount/out
  echo "...done"
else
  echo ./start.bash model_dir input_dir
fi

if [ $1 ] && [ $2 ]
then

  # docker run -v needs absolute paths
  IN=$(realpath $1)
  OUT=$(realpath $2)

  # if input folder doesn't exist, we got a problem
  # if output folder doesn't exist, we can just make it automatically with docker run -v
  if [ ! -f $IN ]
  then
    echo "Input file does not exist: $IN"
    exit 1
  fi

  if [ $3 ]
  then
    MASK=$(realpath $3)

    # if msak file doesn't exist we panic and leave the script
    if [ ! -f $MASK ]
    then
      echo "Mask file does not exist: $MASK"
      exit 1
    fi

    docker run -it -v $IN:/input/input.mrc -v $OUT:/output -v $MASK:/mask/mask.mrc --gpus all zhange5-infp $UID

  else
    # the actual command. $UID is an argument so that ownership of the output folder can be transferred.
    # the 4th arg decides if this skips all the prompts
    docker run -it -v $IN:/input/input.mrc -v $OUT:/output --gpus all zhange5-infp $UID $4
  fi



else
  echo "./start.bash input_mrc output_dir [mask_mrc_file]"

fi

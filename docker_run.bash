#!/bin/bash

# exit the whole thing if keyboard interrupt
trap '{ echo "User cancelled script. exiting..." ; exit 1; }' INT

# the bash script outside of the docker image should have cleared the /output folder already.
# if not, rm -r /output/*
if [ ! $2 ]
then
  if [ ! -z "$(ls -A /output)" ]
  then
    read -p "Output folder is not empty. clear it [y/N]?" clearout
    case "$clearout" in
      [yY][eE][sS]|[yY])
        # clear out folder
          rm -r /output/*
          echo $""
          ;;
      *)
          echo "cancelled. exiting..."
          exit 1
          ;;
    esac
  fi
fi


echo "If the program is hanging (logs do not update), check 'nvidia-smi' to verify gpu has memory."
echo "otherwise, outputfolder/*fm/Pkg*/out.log has the most informative error logs."

if [ ! $2 = auto ]
then
  read -p "press [Enter] to begin." t
fi
echo ""

python3.7 /timing/marktime.py /timing/t0

mkdir /input/tif
cd /input/tif
mrc2tif -c zip /input/input.mrc slice


cd /chlamydia_inf

./run_rbdb.bash &
RBIB_PID=$!

./run_ebib.bash &
EBIB_PID=$!

wait $RBDB_PID
wait $EBIB_PID


cd /output
imodjoin -c rbdb_labels.mod ebib_labels.mod labels.mod
mv rbdb_labels.mod rbdb_pipeline_data/
mv ebib_labels.mod ebib_pipeline_data/

cat rbdbcounts ebibcounts > counts.txt
mv ebibcounts ebib_pipeline_data/
mv rbdbcounts rbdb_pipeline_data/

python3.7 /timing/marktime.py /timing/tf
TOT_TIME=$(python3.7 /timing/timediff.py /timing/t0 /timing/tf)
echo $TOT_TIME > DONE

echo "======================================"
echo "======================================"
echo "              all done!               "
echo "       total time: $TOT_TIME"
echo "======================================"
echo "======================================"

if [ $1 ]
then
  chown -R $1 /output
fi

#!/bin/bash

cd /home/cdeep3m/
./runprediction.sh /pipeline/models/cnn/nrml/ /input/tif /output/nrml
./runprediction.sh /pipeline/models/cnn/edt /input/tif /output/edt
cd /pipeline

# check if there is a mask
if [ -d /mask ]
then
  python3.7 run_pipeline.py -inc_mask /mask/ /output/nrml/ensembled/ /output/edt/ensembled/ /output/
else
  python3.7 run_pipeline.py  /output/nrml/ensembled/ /output/edt/ensembled/ /output/
fi

# apply labels visually
python3.7 get_obj.py

# update csv with volume column
python3.7 add_volume_col.py

# this is the same thing but without volume
rm /output/autoseg_detections_classfied.csv

cd /output
imodauto -E 128 labelled.mrc rb.mod
imodauto -E 255 labelled.mrc db.mod
imodjoin -c rb.mod db.mod rbdb_labels.mod
rm rb.mod db.mod


NUMRB=$(grep "RB$" final.csv | wc -l)
NUMDB=$(grep "DB$" final.csv | wc -l)

echo rb $NUMRB >> rbdbcounts
echo db $NUMDB >> rbdbcounts


mkdir rbdb_pipeline_data
mv labelled.mrc rbdb_pipeline_data/
mv finalstack.mrc rbdb_pipeline_data/
mv final.csv rbdb_pipeline_data/


echo "======================================"
echo "             rbdb done!               "
echo "======================================"

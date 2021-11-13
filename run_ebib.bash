#!/bin/bash

cd /home/cdeep3m/
./runprediction.sh /pipeline/models/cnn/ebib/ /input/tif /output/ebib
cd /pipeline_ebib

python3.7 threshold.py
python3.7 get_csv.py

# apply labels visually
python3.7 make_ebib_prediction.py

# update csv with volume column
python3.7 get_obj_ebib.py

cd /output
imodauto -E 128 ebib_class.mrc eb.mod
imodauto -E 255 ebib_class.mrc ib.mod
imodjoin -c eb.mod ib.mod ebib_labels.mod
rm ib.mod eb.mod


NUMEB=$(grep "0.0,.$" ebib_predictions.csv | wc -l)
NUMIB=$(grep "1.0,.$" ebib_predictions.csv | wc -l)

echo eb $NUMEB >> ebibcounts
echo ib $NUMIB >> ebibcounts


mkdir ebib_pipeline_data
mv ebib_class.mrc ebib_pipeline_data/
mv ebib_finalstack.mrc ebib_pipeline_data/
mv ebib_values.csv ebib_pipeline_data/
mv ebib_predictions.csv ebib_pipeline_data/

echo "======================================"
echo "             ebib done!               "
echo "======================================"

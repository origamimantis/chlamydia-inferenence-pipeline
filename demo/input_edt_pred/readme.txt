
This directory contains files and directories needed to
run Cdeep3M prediction using caffe. Below is a description
of the key files and directories:

1fm,3fm,5fm                 -- Contains results from running prediction.
predict.config              -- Contains path to trained model, and input
                               images.
augimages/                  -- Directory where augmented version of input
                               images will be temporarily stored.
logs/                       -- Contains log files from the 3 worker scripts 
                               running in parallel.
de_augmentation_info.json    -- Contains information on how dataset is
                               broken into packages.
package_processing_info.txt -- Contains summary of number of packages
                               that will be created.


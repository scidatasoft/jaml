# Just Another Machine Learner (JAML)

## TLDR

Main system entities are:
* Files - submitted as SDF or CSV.
* Datasets - created from files by assigning semantic columns values (e.g. record id, continuous value, etc). All structures in datasets are standardized suing one of the chosen standardizers. 
* Models - trained from datasets by selecting the field (binary or continuous), descriptors and ML method. 
* Resultsets (predictions) - similar to datasets, but result in predictions attached as fields/columns.
* Jobs - proxy objects for the actual training or prediction jobs.
* Users - security entities. 


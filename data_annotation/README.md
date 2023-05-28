## *How to annotate Empatica datasets* 

### Step 0: Download Raw Wristband Dataset
GTB/BTC patient data location: https://ibm.ent.box.com/folder/127715947300

For server, save to ***/slow1/raw_datasets/bch/redcap_data***

For Mac, save to ***[Your home folder]/datasets/bch/redcap_data***

### Step 1: Generate Raw Wristband Dataset
Convert raw wristband data to pickle file for each patient.

Run: 

```
# python3 data-annotation/generate_wrst_data.py
```

It will create a folder: ***raw_data*** under ***/slow1/out_datasets/bch/redcap_data_out*** or ***[Your home folder]/datasets/bch/redcap_data_out***and store each patients' raw data separately.

### Step 2: Generate Wristband Annotation Dataset

Run 

```
python3 data-annotation/annotate_wrst_data.py
```

Depending on the configuration, it will create different sub-folders and store labeling in it. In above example it will create:
***case4_non_strict_label_s20_e20***

***case 4*** means offline frequency compensation has been enabled. 

For now we have strict mode and non strict mode. 
1. In strict mode, only those seizures with start timing sync will be annotated. 
2. In non strict mode, except frequent and seizure event as suggested by BCH, all other seizures will be annotated.

To tolerate the timing drift error, we will also add pre-window and post-window at the start and end. 
Windown size has been hard-coded and you need modify code to change.
1. sx: x seconds pre-window added in the start
2. ey: y seconds post-window added in the end


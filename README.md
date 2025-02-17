# nexuscomputewrapper
Wrapper around Nexus compute commands to make the live easier for end user





usage: ncw.py [-h] [-a {STATUS,SUBMIT,DOWNLOAD}] [-f FILE] [-t TOKEN] [-d]

Nexus Compute Wrapper

optional arguments:
  -h, --help                                                        show this help message and exit
  -a {STATUS,SUBMIT,DOWNLOAD}, --action {STATUS,SUBMIT,DOWNLOAD}    Action to perform
  -f FILE, --file FILE                                              Define Actionfile for SUBMIT/DOWNLOAD
  -t TOKEN, --token TOKEN                                           Token File which contains token
  -d, --debug                                                       Debug action turned on





The Nexus Compute Python client delivers a complete set of commands to:
- get overview of Nexus user content (documents, jobs, results)
- submit jobs
- download result files

The wrapper is using the base set of commands (https://nexus.hexagon.com/compute/playground?documentation=true)
to wrap these commands to three main set functionalities as:
- STATUS
- SUBMIT
- DOWNLOAD
to provide the end user a simple entry into the client nexus access.



1) How to login

To reach the Nexus user environment via python cliden a token is needed which is also required by the wrapper.
The text file including the token can be provided by keyword -t or --token. An alternative is a ncwrc file
in the installation directory of ncw that is read automatically if no -t or --token keyword is used. 

The token file is a simple one-liner, for example:
prd:v1.MQR5QRvXwbOuu2R56Alc8x_QOiLIsJPkgAsc8oe_R_vab2uC2xaCEPKYkfj_yEZe3Yn5NMQ_6cdf

A possible usage of the script to test the validation of the token could be:
python ncw.py --token .\token_file.txt
if a explicit token file would be assigned, or:
python ncw.py
which would read automatically the ncwrc file



2) Get Status Information

To get a STATUS information from Nexus environment, the selected action should be: STATUS

A possible usage of the script to get the status in the user Nexus environment could be:
python ncw.py --action STATUS

The status infomation are printed into startup terminal and saved in a file: ncw_output_status.txt
in startup directory. The status file contains information about existind Nexus documents, jobs and
computed results.



3) Submit Job(s)

With the SUBMIT action keyword single or multiple jobs can be started. To provide the detailed
information what should be calculated a submission file should be provided.

A possible usage of the script to submit files via Nexus compute python client wrapper could be:
python ncw.py --action SUBMIT --file ncw_submit_file.txt

A sample submit file could be:
doc:doc_name
job:job_name
file:a1.dat
file:a2.dat

If there is no document name, a document name including time stamp is created, if there are not enough job names, the last job name is used with an additional counter, 
if there is no job name also the time stamp is used to create a sample job name. 

A minimum required submit file would be for example:
file:a1.dat
file:a2.dat
containing the analysis files.

After job submission in Nexus environment an output file is created that contains also document IDs 
and job IDs that are needed later in case of downloading results. So some lines in submit output file 
could be for example:
DOC_ID:f78149a5-9382-47cb-bf4b-6978624c3a23
 JOB_ID:34c0aa3c-e9d5-95ad-1f08-c440b4f397bd
 JOB_ID:1ee30e44-2fa1-c5a7-a8af-66b08ae97487

The created submit output file can be used directly for downloading results due to these formatted
document and job ID lines.


# nexuscomputewrapper
Wrapper around Nexus compute commands to make the live easier for end user

Nexus Compute delivers a complete set of commands to:
- get overview of Nexus user content (documents, jobs, results)
- submit jobs
- download result files

The wrapper is using the base set of commands (https://nexus.hexagon.com/compute/playground?documentation=true)
to wrap these commands to three main set functionalities as:
- STATUS
- SUBMIT
- DOWNLOAD
to provide the end user a simple entry into the client nexus access.


How to login:

To reach the Nexus user environment via python cliden a token is needed which is also required by the wrapper.
The text file including the token can be provided by keyword -t or --token. An alternative is a ncwrc file
in the installation directory of ncw that is read automatically if no -t or --token keyword is used. 

A possible usage of the script to test the validation of the token could be:






to get a STATUS information from Nexus environment, the selected action should be: STATUS


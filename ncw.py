import os, sys, string, argparse
from datetime import datetime
import threading
from nexuscompute import NexusCompute
from nexuscompute.Enums import JobStatus

# ---------------------------------------------------------------------------------------

class NCW():
    """
    nexus compute wrapper class
      
    wapper around the basic commands to setup common requests
    """

    def __init__(self, arg_space):
        """
        init
        
        initialize class and define attributes and methods
        """
        self.nc=NexusCompute()
        self.arg_space = arg_space
        self.token = ""
        self.listening_port = None
        self.my_user = None
        # get into nexus compute environment
        self.get_token()
        self.start()
        self.login()
        


    def get_token(self):
        """
        get_token 
        
        get token from token file or from rc file
          - via explicit named token file in argument list
          - automatically via rc file: ncwrc
        """
        # variables
        return_value = 0
        # (1) token file definition 
        if self.arg_space.token:
            try:
                file_in = open(self.arg_space.token,'r')
                line_list = file_in.readlines()
                file_in.close()
                self.token = line_list[0].strip()
            except:
                pass
            print ("token from token file: ", self.token)
        # (2) do we have an token rc file
        if self.arg_space.token == None:
            try:
                file_in = open(os.path.dirname(os.path.realpath(__file__)) + "/ncwrc","r")
                line_list = file_in.readlines()
                file_in.close()
                self.token = line_list[0].strip()
                print ("rc token: ", self.token)
            except:
                pass
        # no token definition
        if self.token == "":
            print ("ERROR: no token definition")
            sys.exit(1)
            return_value = 1
        #
        return return_value
        


    def start(self):
        """
        start

        spawn NodeJS process and connect
        as result a listening port is delivered
        """
        self.listening_port = self.nc.start()
        print ("port: ", self.listening_port)



    def login(self):
        """
        login
        
        with the token (from token file or rc file) the user is logged in
        """
        user_id = 0
        self.my_user = self.nc.login(self.token)
        try:
            print ("user id: ", self.my_user.loginRefId)
        except:
            pass
             


    def end_nc(self):
        """
        end_nc
        
        end of nexus compute process
        """
        self.my_user.logoff()
        self.nc.stop()
        

 


# STATUS ================================================================================
    
    def get_user_status(self):
        """
        get nexus user status
        
        several information in nexus environment as user could be interesting:
        - all user documents
        - all jobs calculated in documents
        - status of jobs in documents
    
        next chapters could be:
        - what for result files per job
        - available software configurations for example for Nastran, what queues ...
        """
        return_list = []
        solver_configs = {}
        # list of documents
        doc_list = self.my_user.list_documents()
        return_list.append("number of documents: " + str(len(doc_list)))
        for entry_dict in doc_list:
            return_list.append("  ")
            doc_id = entry_dict['id']
            doc_name = entry_dict['name']
            return_list.append(" doc name/id: " + doc_name + "      " + doc_id)
            # load according document to reach further information as jobs and files
            doc_obj = self.my_user.load_document(doc_id)
            # get job information
            job_dict = doc_obj.list_jobs()
            return_list.append("  number of jobs: " + str(len(job_dict)))
            for job_id, job_feat in job_dict.items():
                return_list.append("   job name/id/status: "+job_feat['name']+"  " +job_id+"  "+str(job_feat['status']))
            # get file information
            files_in_doc = doc_obj.list_files()
            return_list.append("  files in document:")
            for entry in files_in_doc:
                return_list.append("   " + str(entry))
            # solver configurations
            if len(solver_configs) == 0:
                solver_configs = doc_obj.get_solver_configs()
            doc_obj.close()
            # after document listing the solve configuration is attached
        return_list.append("\n\nsolver configurations:")
        for solver,v1 in solver_configs.items():
            if solver == "nastran":
                for k2,v2 in v1.items():
                    if k2 == "versions" or k2 == "configs":
                        for k3,v3 in v2.items():
                            return_list.append("  " + str(solver) + " " + str(k2) + " " + str(k3))         
        #
        file_out = open("ncw_output_status.txt","w")
        file_out.writelines([l+"\n" for l in return_list])
        file_out.close()                            
        # return all information as list
        return return_list




    def get_user_information(self):
        print ("get user information ...")
        print (type(self.my_user), dir(self.my_user))
        doc_list = self.my_user.list_documents()
        print ("number of documents: " + str(len(doc_list)))
        for entry_dict in doc_list:
            print (entry_dict['id'], " - ", entry_dict['name'])
        


# SUBMIT ================================================================================
    


    def submit_files(self):
        """
        submit files

        - reads a submission file
        - create document and job(s)
        - transfer analysis files to Nexus compute cloud
        - submit jobs

        during doc creation and job submission several IDs are created,
        these will be saved later in a log file that can be used
        """
        print ("submit files ...")
        submit_dict = get_submission_info(self.arg_space.file)
        # variables
        log_lines = []
        file_names = []
        job_names = []
        # solver configurations
        solver_name     = 'nastran'
        hardware_config = 'medium'
        version         = '2024.2'
        # all previously collected submission infomation into log file
        log_lines.append("collected submission information:")
        for k,v in submit_dict.items():
            print (k,v)
            if k == 'DOC'  or  k == "CALC_DIR": 
                log_lines.append(str(k))
                log_lines.append(" " + str(v))
            if k == 'JOBS' or k == 'CALC_FILES':
                log_lines.append(k)
                for entry in v:
                    log_lines.append(" " + str(entry))
        # if there are no analysis files left, exit with error file
        if len(submit_dict['CALC_FILES']) == 0:
            print ("ERROR: no calc files for submission defined ...")
            write_report_file(submit_dict, "ncw_output_submit.err", "CR", "PRINT")
            sys.exit(1)
        # create and load document in nexus
        doc_id = self.my_user.new_document(submit_dict['DOC'])
        doc_obj = self.my_user.load_document(doc_id)
        print ("loaded document into memory: ", doc_id)
        # upload files and prepare local file names
        print ("uploading files ...")
        log_lines.append("uploading analysis files ...")
        for local_file_name in submit_dict['CALC_FILES']:
            local_dir, file_name = os.path.split(local_file_name)
            log_lines.append("  " + local_file_name + " " + file_name)
            doc_obj.upload_file(local_file_name, file_name, progress)
            file_names.append(file_name)
        # submit jobs
        job_names = submit_dict['JOBS']
        log_lines.append("DOC_ID:"+doc_id)
        log_lines.append("CALC_DIR:"+submit_dict["CALC_DIR"])
        for i,job in enumerate(job_names):
            job_id = doc_obj.submit_job(job_name=job, 
                solver=solver_name, solver_version=version, hardware=hardware_config, 
                nb_nodes=1, files=[file_names[i]], 
                command="nast20242 mem=100mb smp=1 dmp=1 scr=yes sdir=../scratch "+file_names[i], 
                max_runtime_hours=1, dry_run=False)
            print ("submitted: ", job, " job_id: ", job_id)
            log_lines.append("submitted " + job + " with file " + file_names[i])
            log_lines.append(" JOB_ID:" + job_id)
        # close open document
        doc_obj.close()
        # write log file
        file_out = open("ncw_output_submit.txt", 'w')
        file_out.writelines([l+"\n" for l in log_lines])
        file_out.close()
        # send back document object
        return doc_obj




# DOWNLOAD ==============================================================================
    


    def download_files(self):
        """
        download files

        - reads a download file
        - try to download files from definitions in download file

        needed information would be a document id and job ids
        the calc directory is used to store the files locally
        """
        print ("download files ...")
        download_dict = get_download_info(self.arg_space.file)
        for k,v in download_dict.items():
            print ("   ", k,v)
        # if there are no analysis files left, exit with error file
        if len(download_dict['JOB_IDS']) == 0:
            print ("ERROR: no job ids for download defined ...")
            write_report_file(download_dict, "ncw_output_download.err", "CR", "PRINT")
            sys.exit(1)
        # variables
        log_lines = []
        doc_id = download_dict["DOC_ID"]
        job_ids = download_dict["JOB_IDS"]
        calc_dir = download_dict["CALC_DIR"]
        log_lines.append("doc ids and job ids:")
        log_lines.append(" " + str(doc_id))
        for j in job_ids:
            log_lines.append("  " +  str(j))
        log_lines.append("calc dir: " + calc_dir)
        # get files from document and jobs
        doc_obj = self.my_user.load_document(doc_id)
        job_dict = doc_obj.list_jobs()
        print ("get files from doc/jobs ...")
        for job_id in job_ids:
            job_name = job_dict[job_id]['name']
            print ("start download of files from job_id/job_name: ", job_id, " / ", job_name)
            log_lines.append("start download of files from job_id/job_name: "+job_id+" / "+job_name)
            job_result_files = doc_obj.list_job_results(job_id)
            print ("content of job result files ...")
            # create locally the result directory
            local_res_dir = calc_dir + "/" + "compute/results/" + job_name
            os.makedirs(local_res_dir, exist_ok=True)
            # loop ove all result files, download to local
            for job_file in job_result_files:
                target = calc_dir + "/" + job_file  
                print ("  ",target)
                log_lines.append("  " + target)
                status = doc_obj.download_file(document_path=job_file,sink=target,progress=download_progress)      
                print ("status: ", status)
        # close open document
        doc_obj.close() 
        # write log file
        file_out = open("ncw_output_download.txt", 'w')
        file_out.writelines([l+"\n" for l in log_lines])
        file_out.close()





# =======================================================================================





def get_help():
    """
    get help
    """
    print (" ")
    print ("Nexus Compute Wrapper")
    print (" ")
    print ("options:")
    print ("--action   <ACTION>     STATUS/SUBMIT/DOWNLOAD")
    print ("--file     <FILENAME>   needed for SUBMIT/DOWNLOAD")
    print ("--token    <TOKENFILE>  contains token")
    print (" ")
    print ("use optional ncwrc  or  .ncwrc  file to activate token without token argument")
    print (" ")
    print ("examples running script: ")
    print ("   --action=SUBMIT --file=submit_file.txt")
    print ("   --action=STATUS --token=token_file.txt")
    print (" ")





def arg_handler():
    """
    argument handler
    
    possible arguments:
        -h --help
        -a --action   ACTION  ('STATUS','SUBMIT','DOWNLOAD')
        -f --file     action_file_name
        -t --token    token_file_name    
    if actions are: SUBMIT, DOWNLOAD a file is needed, which defines further information for this action
    """
    dir_current = os.getcwd()
    dir_script = os.path.dirname(os.path.realpath(__file__))
    term_program = os.getenv("TERM_PROGRAM")
    # setup of argparse
    parser = argparse.ArgumentParser(description='Nexus Compute Wrapper')
    parser.add_argument('-a', '--action', choices=['STATUS','SUBMIT','DOWNLOAD'], help='Action to perform')
    parser.add_argument('-f', '--file', help='Define Actionfile for SUBMIT/DOWNLOAD')
    parser.add_argument('-t', '--token', type=str, help='Token File which contains token')
    parser.add_argument('-d', '--debug', action="store_true", help='Debug action turned on')
    args = parser.parse_args()            
    # debug information
    if args.debug:
        print ("========== DEBUG is ON ...")
        print (dir_current)
        print (dir_script)
        print (term_program)
        print (type(parser), type(args))
        print ("ARGUMENTS: ", args)
        print ("ARG VARs:  ", args.action, args.file, args.token, args.debug)
        print ("==========")
    # action handling, SUBMIT and DOWNLOAD require an action file 
    if args.action:
        print (args.action)
        if args.action == "SUBMIT" or args.action == "DOWNLOAD":
            print (args.file)
            if os.path.exists(args.file):
                print (" action file found...")
            else:
                print (" ERROR: action file not found ...\n")
                args = parser.parse_args(['-h'])               
    # token handling      
    if args.token:
        print (args.token)
        if os.path.exists(args.token):
            print (" token file found ...")
        else:
            print (" WARNING: token file not found ...")
    if not args.token:
        print ("no args.token, try to read rc token file ...")
        if os.path.exists(dir_script + "/ncwrc"):
            print (" rc token file found ...")
        else: 
            print (" rc token file not found ...\n")
            args = parser.parse_args(['-h'])                           
    # return argparse Namespace object         
    return args
 




def progress(speed, elapsed_time, transferred_size):
    """
    upload progress
    """
    s = str(speed/1000**2)
    e = str(elapsed_time)
    t = str(transferred_size/1000**2)
    # with open('save_job_status_messages.txt','a') as status_file:
    #    status_file.write(s + "  " + e + "  " + t + "\n")
    # print ("%.2fMB/s %.2fs %.2fMB" % (speed/1000**2, elapsed_time, transferred_size/1000**2))





def download_progress(transferred_size, total_size, speed, elapsed_time):
    """
    download progress
    """
    progress = transferred_size / total_size * 100  # percentage
    # with open('save_job_status_messages.txt','a') as status_file:
    #     status_file.write(str(speed/1000**2) + "  " + str(elapsed_time) + "  " + str(transferred_size/1000**2) + "\n")
    # print("%.2f%% %.2fMB/s %.2fs %.2fMB" %(progress, speed/1000**2, elapsed_time, transferred_size/1000**2))    





def write_report_file(output_list, file_name, cr, print_flag):
    """
    write report file
    
    with file name a line list will be written into file
    CR argument decides, whether a carriage return is written for each line

    if the print flag is set, then the content will be printed

    in case of dict instead of list to be printed, the dict will be converted 
    into a list with key and value

    output_list - dict or list
    file_name   - file_name that is created
    cr          - carriage return flag
    print_flag  - print flag
    """
    # variables
    line_list = []
    # set carriage return
    if cr == "CR":
        cr = "\n"
    else:
        cr = ""
    # if output list is a dictionary
    if isinstance(output_list, dict):
        for k,v in output_list.items():
            line_list.append(str(k) + "  " + str(v))
    if isinstance(output_list, list):
        line_list = output_list
    # print if required
    if print_flag == "PRINT":
        for line in line_list:
            print (line)
    # write content to file
    file_out = open(file_name,"w")
    file_out.writelines([l+cr for l in line_list])
    file_out.close()    





def get_submission_info(submit_info_file):
    """
    get submission info
    
    for analysis a submit_info_file is read that contains information
    as document name, job name and analysis file names

    if there is no document name a default name is provided
    if there are no job names, some default job names are provided

    the directory of submit info file is assumed as the same directory where the analysis files
    are stored except the analysis file definition contains a dedicated directory,
    for example:
        file:a1.dat
        file:a2.dat
    means, that these files are located in the same directory of submit_info_file,
    and with:
        file:c:/tmp/dir_a1/a1.dat
        file:c:/tmp/dir_a2/a2.dat
    the directory of the file definition is used to upload the file to nexus environment

    the complete infomation is stored in a dictionary for further usage
    """
    # startup info
    print ("get submission info from file: ", submit_info_file)
    current_dir = os.getcwd()
    print (current_dir)
    # variable definition
    return_dict = {"DOC":"","CALC_DIR":"","JOBS":[],"CALC_FILES":[], "ERRORS":[]}
    job_list = []
    file_list = []
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    # split in calc_dir and according files
    calc_dir, info_file = os.path.split(submit_info_file)
    # print ("splitted calc dir and info file: ", calc_dir, info_file)
    return_dict["CALC_DIR"] = calc_dir
    # read submission info file
    file_in = open(submit_info_file,'r')
    line_list = file_in.readlines()
    file_in.close()
    # collect and assign infos to dictionary
    for line in line_list:
        line = line.strip()
        entry_list = line.split(':')
        if entry_list[0].upper() == "DOC":
            return_dict["DOC"] = entry_list[1]
        if entry_list[0].upper() == "JOB":
            return_dict["JOBS"].append(entry_list[1])
        if entry_list[0].upper() == "FILE":
            if "/" in line or "\\" in line:
                file_to_check = line[5:].strip()
            else:
                if len(return_dict["CALC_DIR"]) > 0:
                    file_to_check = return_dict["CALC_DIR"] + "/" + entry_list[1]
                else:
                    file_to_check = entry_list[1]
            # check file existance
            if os.path.exists(file_to_check):
                print (" file check: ", file_to_check, "  PASSED")
                return_dict["CALC_FILES"].append(file_to_check)
            else:
                print (" ERROR: ", file_to_check, " does not exist")
                return_dict["ERRORS"].append("ERROR: "+file_to_check+" does not exist")
    # clean up and fill up the dictionary with defaults if needed
    # assign doc if does not exist and get job_list and file_list, assign job if no job 
    for k,v in return_dict.items():
        if k == "DOC" and len(v)==0:
            return_dict["DOC"] = "doc_" + current_time
        if k == "JOBS":
            job_list= v
        if k == "CALC_FILES":
            file_list = v
    if len(job_list) == 0:
        job_list.append('job_' + current_time)
    # to less job names available, fill them up
    if len(job_list)<len(file_list):
        last_job_name = job_list[len(job_list)-1]
        for i in range(len(file_list)-len(job_list)):
            job_list.append(last_job_name + "_" + str(i+1))
        return_dict["JOBS"] = job_list
    # number of jobs is greater then number of files, reduce jobs
    if len(job_list) > len(file_list):
        for i in range(len(job_list)-len(file_list)):
            job_list.pop()
    # dictionary with doc, job, analysis file information
    return return_dict





def get_download_info(download_file):
    """
    get download info

    if files needs to be downloaded a document id and a job id is needed,
    all these information are saved into submission log file,
    if that is not available, the ids can be grabbed from the status information 

    an example download file could be (containing doc id, job id and optional calc dir):
    DOC_ID:c380b241-d3dd-49c4-ae0d-0626c5f79abd
    CALC_DIR:c:/tmp/python/nexus/dir_analysis
    JOB_ID:28d999e4-e147-60fb-d905-9c0a454713ea
    JOB_ID:3e49a037-1407-f897-396b-82dece509ad6
    """
    # variables
    return_dict = {"DOC_ID":"","CALC_DIR":".","JOB_IDS":[]}
    # read submission info file
    file_in = open(download_file,'r')
    line_list = file_in.readlines()
    file_in.close()
    # sort lines in dictionary
    for line in line_list:
        line = line.strip()
        if ":" in line:
            entry_list = line.split(':')
            if entry_list[0].strip() == 'DOC_ID':
                return_dict['DOC_ID']=entry_list[1].strip()
            if entry_list[0].strip() == 'JOB_ID':
                return_dict['JOB_IDS'].append(entry_list[1].strip())
            if entry_list[0].strip() == 'CALC_DIR':
                return_dict['CALC_DIR']=line[9:].strip()
    # return according dictionary
    return return_dict





# =======================================================================================





def main():
    """
    main function


    """
    # argument handling
    args = arg_handler()
    print ("MAIN:",args.action, args.file, args.token)
    # instance of object, connect to nexus as a user
    ncw = NCW(args)
    # actions
    # STATUS
    if args.action == "STATUS":
        status_list = ncw.get_user_status()
        for line in status_list:
            print (line)
    # SUBMIT
    if args.action == "SUBMIT":
        ncw.submit_files()
    # DOWNLOAD
    if args.action == "DOWNLOAD":
        ncw.download_files()
    # logout and end process
    ncw.end_nc()





# =======================================================================================
if __name__ == "__main__":
    main()   
   
# =======================================================================================

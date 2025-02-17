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
        



# ---------------------------------------------------------------------------------------


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
    if args.action == "STATUS":
        status_list = ncw.get_user_status()
        for line in status_list:
            print (line)
    

    # logout and end process
    ncw.end_nc()






# =======================================================================================
if __name__ == "__main__":
    main()   
   
# =======================================================================================





# storage:
#    # use argument file, help or command line arguments
#    if len(sys.argv) <= 1:
#        try:
#            file_in = open(dir_script + '/arguments.txt','r')
#            line_list = file_in.readlines()
#            file_in.close()
#            argument_list = [ e.strip() for e in line_list ]
#            print (argument_list)
#            args = parser.parse_args(argument_list)
#        except: 
#            args = parser.parse_args(['-h'])
#    else:


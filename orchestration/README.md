nap-core orchestration    

###core-api提供借口    

+ 创建用户      
    方法名： create_user      
    方法位置： from compose import app_info      
    方法参数： username, password      
    返回值： True, False      

+ 删除用户      
    方法名： delte_user      
    方法位置： from compose import app_info      
    方法参数： username      
    返回值： false or true      

+ project 列表      
    方法名： project_list      
    方法位置： from compose import app_info      
    方法参数： username, password, begin, length      
    返回值： list[]      

+ service列表      
    方法名： service_list      
    方法位置： from compose import app_info      
    方法参数： username, password, project_name      
    返回值： list[dict{name:xxx, ip:xxx, status:xxx, port:{}}]      

+ 从git创建项目      
    方法名： create_project_from_url      
    方法位置： from compose import project_create      
    方法参数： username, password, project_name, url      
    返回值： "Argv", list[] or "True" "sucess" or "False" "why "      

+ 从filebrowser创建项目      
    方法名： create_project_from_file      
    方法位置： from compose import project_create      
    方法参数： username, password, project_name     
    返回值： "Argv", list[] or "True" "sucess" or "False" "why "      

+ 删除项目      
    方法名： delete_project        
    方法位置： from compose import app_info      
    方法参数： username, password, project_name      
    返回值： True or False      

+ 获取日志      
    方法名： get_logs      
    方法位置： from compose import app_info      
    方法参数： username, password, project_name, service_name      
    返回值： String      

+ 填参数      
    方法名： replace_argv      
    方法位置： from compose import project_create      
    方法参数： username, password, project_name, argv[]      
    返回值： True "success create project " or False "create project failed and why"      

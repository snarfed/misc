#!/usr/bin/env python

"""
This is a python script for retrieving Google Tasks 
Usage: 
    -e or --email [email] 
        Your Google Account or Google Apps email 
    -p or --password [password] 
        Your password 
    -b or --bullet [bullet] 
        Bullet for tasks list. Default is '*'

Example:
    google_tasks.py -e bob@gmail.com -p yaroslavl -b --

Thank you Scott Hillman for the implementation of Google Authentication
http://everydayscripting.blogspot.com/2009/10/python-fixes-to-google-login-script.html

Evgeny Pavlov, http://evgeny.tel
"""

import urllib
import urllib2
import htmllib
import htmlentitydefs
import getpass
import re
import sys
import getopt


def unescape(text):
    """Removes HTML or XML character references 
       and entities from a text string
       
       From Fredrik Lundh
       http://effbot.org/zone/re-sub.htm#unescape-html
       
       Little bit modified
    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # Character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                print "Error with encoding HTML entities"
                pass
        else:
            # Named entity
            text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)
    
    
def main(argv):
    """ Get arguments: email, password and type of bullet """
    
    bullet = '* '
    email =  ''
    password = ''
    add = None

    try:
        opts, args = getopt.getopt(argv, "he:p:b:a:", ["help", "email=", "password=", "bullet=", "add="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-e", "--email"):
            email = arg
        elif opt in ("-p", "--password"):
            password = arg
        elif opt in ("-b", "--bullet"):
            bullet = arg
        elif opt in ("-a", "--add"):
            add = arg
    
    return (email, password, bullet, add)
    

def usage():
    """ Help and the list of arguments for this script """
    
    print """This is a python script for retrieving Google Tasks 
Usage: 
    -e or --email [email] 
        Your Google Account or Google Apps email 
    -p or --password [password] 
        Your password 
    -b or --bullet [bullet] 
        Bullet for tasks list. Default is '*'

Example:
    google_tasks.py -e bob@gmail.com -p yaroslavl -b --

Evgeny Pavlov, http://evgeny.tel"""

if __name__ == "__main__":
    # Arguments
    (email, password, bullet, add) = main(sys.argv[1:])

    # Google Account or Google Apps
    email_split = email.split('@')
    try:
        email_domain = email_split[1]
    except:
        print 'Incorrect email address!\n'
        usage()
        sys.exit()
    if email_domain in ('googlemail.com', 'gmail.com', 'google.com'):
        google_apps = 0
    else:
        google_apps = 1
        email = email_split[0]
    
    # Initialization  
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    urllib2.install_opener(opener)
    
    # Define URLs
    if google_apps:
        login_page_url = 'https://www.google.com/a/%s/ServiceLogin' % email_domain
        auth_url = 'https://www.google.com/a/%s/LoginAction2' % email_domain
        tasks_url = 'https://mail.google.com/tasks/a/%s/m' % email_domain
    else:
        login_page_url = 'https://www.google.com/accounts/ServiceLogin'
        auth_url = 'https://www.google.com/accounts/ServiceLoginAuth'
        tasks_url = 'https://mail.google.com/tasks/m'
    
    # 1. Load login page
    login_page_content = opener.open(login_page_url).read()
    
    # Find GALX value
    galx_match_obj = re.search(r'name="GALX"\s*value="([^"]+)"', login_page_content, re.IGNORECASE)
    
    galx = galx_match_obj.group(1) if galx_match_obj.group(1) is not None else ''
    
    # Set up login credentials
    login_params = urllib.urlencode( {
       'Email' : email,
       'Passwd' : password,
       'continue' : tasks_url,
       'GALX': galx
    })
    
    # 2. Login
    opener.open(auth_url, login_params)

    # 3. Open Tasks home page
    tasks_content = opener.open(tasks_url).read()
    
    # Check signing in
    key = re.search('create_tasks', tasks_content)
    if not key:
        print 'Check your credintals!'
        sys.exit()
    
    # Retrieve list ids
    tasks_content_split_obj = re.search(r'<select(.*?)select>', tasks_content, re.IGNORECASE)
    tasks_content_split = tasks_content_split_obj.group(1)
    listids = re.findall(r'[0-9]{20}:[0-9]:[0-9]', tasks_content_split)
    
    if add is not None:
        # add new task
        data = "security_token=AOobzdUovRnTf5bfrN8xr1lsgyzoLvoNJA:1273819631247&actt=create_tasks&numa=5&tkn1=%s&tkn2=&tkn3=&tkn4=&tkn5=&pid=04291589652955054844:0:0" % add
        opener.open(tasks_url, urllib.quote(data))
    
    # 4. Fetch all lists
    for listid in listids:
        # List content
        list_content = opener.open(tasks_url + "?listid=%s" % listid).read()
    
        # Only tasks remain
        list_content_split_obj = re.search('(.*?)name="numa"', list_content, re.IGNORECASE | re.DOTALL)
        list_content_split = list_content_split_obj.group(1)
    
        # Get Tasks in <tr></tr>
        tasks_in_tr = re.findall(r'<tr(.*?)tr>', list_content_split, re.IGNORECASE | re.DOTALL)
    
        # Work with this dirty tasks
        for task_in_tr in tasks_in_tr:
            # Retrieve task
            task_obj = re.search(r'<td class="text">(.*?)</td>', task_in_tr, re.IGNORECASE)
            if not task_obj:
                continue
            task = task_obj.group(1)
    
            # Indent
            indent = len(re.findall(r'<td class="checkbox"', task_in_tr)) - 1
    
            # HTML entities
            task = unescape(task)
            task = task.strip()
    
            # 5. At last output
            if task  != '': 
                print '  ' * indent, bullet, task

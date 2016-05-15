import os
import shutil
import sys
import json
from invoke import task
from invoke import run
from invoke import Context


DIR_SSH = "%s/.ssh" % os.path.expanduser("~")
SSH_FILENAME = "cloudlet_rsa"
SSH_SIGNATURE = "openedgecomputing@cmu.edu"
OLD_AUTHORIZEDKEY_FILE = "authorized_keys.old"
DIR_DEVSTACK = "./devstack"
DIR_EXTENSION = './elijah-openstack'

# temp file
TEMP_DIR = "/tmp/cloudlet-install/"

def setup():
    global DIR_SSH
    global SSH_FILENAME

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    run("mkdir %s" % TEMP_DIR)

    # register rsa key for myself
    if not os.path.exists(DIR_SSH):
        run("mkdir %s" % DIR_SSH)
        chmod("mkdir -m 700 %s" % DIR_SSH)
    old_pwd = os.getcwd()
    os.chdir(DIR_SSH)
    run("ssh-keygen -f %s -t rsa -N '' -C \"%s\"" % (SSH_FILENAME, SSH_SIGNATURE))
    pubkey_str = open(SSH_FILENAME + ".pub", 'r').read()
    if os.path.exists("./authorized_keys") is False or\
            run('grep "%s" authorized_keys' % pubkey_str, warn=True).return_code != 0:
        run("cat %s.pub >> authorized_keys" % (SSH_FILENAME))
        run("chmod 600 authorized_keys")
    os.chdir(old_pwd)


def teardown():
    global DIR_SSH
    global SSH_FILENAME
    global SSH_SIGNATURE

    ssh_file = os.path.join(DIR_SSH, SSH_FILENAME)
    author_key = os.path.join(DIR_SSH, "authorized_keys")
    if os.path.exists(ssh_file):
        os.remove(ssh_file)
        os.remove(ssh_file + ".pub")
    if run('grep "%s" %s' % (SSH_SIGNATURE, author_key), warn=True, hide='stdout').return_code == 0:
        run("sed -i '/%s/d' %s" % (SSH_SIGNATURE, author_key), warn=True, hide='stdout')

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)


@task
def install_cloudlet_library():
    global DIR_SSH
    global SSH_FILENAME

    # basic library
    run("sudo apt-get update")
    run("sudo apt-get install -y git openssh-server fabric")

    DIR_PROVISIONING = 'provisioning'
    if os.path.exists(DIR_PROVISIONING):
        shutil.rmtree(DIR_PROVISIONING)
    run("git clone https://github.com/cmusatyalab/elijah-provisioning/ %s"\
        % DIR_PROVISIONING)
    old_pwd = os.getcwd()
    os.chdir(DIR_PROVISIONING)
    run("fab install -i %s" % os.path.join(DIR_SSH, SSH_FILENAME))
    os.chdir(old_pwd)


@task
def patch_openstack():
    global DIR_SSH
    global SSH_FILENAME

    if os.path.exists(DIR_EXTENSION):
        shutil.rmtree(DIR_EXTENSION)
    run("git clone https://github.com/cmusatyalab/elijah-openstack %s"\
        % DIR_EXTENSION)
    old_pwd = os.getcwd()
    os.chdir(DIR_EXTENSION)
    run("fab localhost devstack_single_machine -i %s" % os.path.join(DIR_SSH, SSH_FILENAME))
    os.chdir(old_pwd)


@task
def install_openstack():
    global DIR_DEVSTACK

    LOCAL_CONF_URL = "https://gist.githubusercontent.com/krha/2bc593679132f8cee0d2/raw/cb97cba56d6fd9cf5dde094af3b67a1dffebb2e2/loca"

    # create virtual NIC for internal network of OpenStack
    run("sudo modprobe dummy")
    run("sudo ip link set name eth9 dev dummy0", warn=True, hide='stderr')
    if run('grep dummy /etc/modules', warn=True, hide='stdout').return_code != 0:
        run("echo dummy | sudo tee -a /etc/modules", hide='stdout')
    if run('grep dummy /etc/rc.local', warn=True, hide='stdout').return_code != 0:
        run("sudo sed -i '/^exit 0/i ip link set name eth9 dev dummy0' /etc/rc.local" , warn=True, hide='stderr')

    # clone openstack
    if os.path.exists(DIR_DEVSTACK):
        shutil.rmtree(DIR_DEVSTACK)
    ret = run("sudo grep \"$USER ALL=(ALL) NOPASSWD\" /etc/sudoers", warn=True)
    if ret.return_code != 0:
        run("sudo echo \"$USER ALL=(ALL) NOPASSWD: ALL\" | sudo tee -a /etc/sudoers",
            hide='stdout')
    run("git clone https://github.com/openstack-dev/devstack -b stable/kilo %s"\
        % DIR_DEVSTACK)
    run("wget --no-check-certificate %s -O %s" %\
        (LOCAL_CONF_URL, os.path.join(DIR_DEVSTACK, "local.conf")))
    run("sed -i 's/eth0/em1/g' %s" % os.path.join(DIR_DEVSTACK, "local.conf"))
    run("sed -i 's/eth1/eth9/g' %s" % os.path.join(DIR_DEVSTACK, "local.conf"))
    run("cd %s && ./stack.sh" % DIR_DEVSTACK)


@task
def restart_openstack():
    run("./restart.sh", use_pty=True, warn=True)
    #run("ps aux | grep keystone-all")
    #run("screen -S stack -X screen -t keystone bash")
    #run("screen -S stack -X stuff $'keystone-all\\n'")


@task
def import_basevm():
    global TEMP_DIR
    global DIR_DEVSTACK
    global DIR_EXTENSION

    TEMP_BASE_VM_FNAME = os.path.join(TEMP_DIR, "precise-hotplug.zip")
    TEMP_CREDENTIAL_FILE = os.path.join(TEMP_DIR, "credential.openstack")
    BASE_VM_URL = "https://storage.cmusatyalab.org/cloudlet-vm/precise-hotplug.zip"
    BASE_VM_HASH = "abda52a61692094b3b7d45c9647d022f5e297d1b788679eb93735374007576b8"

    run("wget --no-check-certificate %s -O %s" % (BASE_VM_URL, TEMP_BASE_VM_FNAME))
    grep_strs = [('account', 'OS_USERNAME'), ('password', 'OS_PASSWORD'), ('tenant', 'OS_TENANT_NAME')]
    ret_dict = {'server_addr':'127.0.0.1'}
    openstack_envfile = os.path.join(DIR_DEVSTACK, "accrc", "demo", "admin")
    for (key, grep_str) in grep_strs:
        ret = run("grep %s %s" % (grep_str, openstack_envfile), hide='both')
        value = ret.stdout.split("=")[-1].strip()[1:-1]
        ret_dict[key] = value
    with open(TEMP_CREDENTIAL_FILE, "w") as f:
        f.write(json.dumps(ret_dict))
    sys.stdout.write("Start import Base VM to OpenStack. This may take a while.\n")
    sys.stdout.write("-"*70 + "\n")
    run('%s -c %s import-base %s ubuntu' % (
        os.path.join(DIR_EXTENSION, "client", "cloudlet_client.py"),
        TEMP_CREDENTIAL_FILE,
        TEMP_BASE_VM_FNAME)
    )


def success_message():
    global DIR_DEVSTACK

    ret = run("grep ADMIN_PASSWORD= %s" %\
              os.path.join(DIR_DEVSTACK, "local.conf"), hide='both')
    password = ret.stdout.split("=")[-1].strip()
    sys.stdout.write(("\n------------------------------------------------------\n"
                      "Congradulations! OpenStack++ is successfully installed.\n\n"
                      "Login to OpenStack Dashboard at http://localhost/\n"
                      "Here's your account information (See more at ./devstack/local.conf):\n"
                      "ID: admin\n"
                      "password: %s\n\n" % password
                      ))
    sys.stdout.write("Remember to use ./restart.sh script to restart OpenStack or after the system reboot\n")


@task
def install():
    print("Start install!")
    try:
        setup()
        install_openstack()
        install_cloudlet_library()
        patch_openstack()
        restart_openstack()
        import_basevm()
        success_message()
    except Exception as e:
        sys.stderr.write(str(e))
        return 1
    finally:
        teardown()
    return 0

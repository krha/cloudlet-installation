Elijah: Cloudlet Infrastructure for Mobile Computing
========================================================

This is an installation script of
[Cloudlet-Openstack](https://github.com/cmusatyalab/elijah-openstack) for those
users who are does not have experience on OpenStack or Cloudlet
library.

It is important to note that this script is not covering all corner cases that can happen because of different hardware/network situations. It assume that you start running the script from a **[Ubuntu 14.04.3 LTS release](http://old-releases.ubuntu.com/releases/14.04.3/ubuntu-14.04.3-server-amd64.iso)**

For more cloudlet information, please visit our project web page at at [Elijah
page](http://elijah.cs.cmu.edu/) or read Wikipedia page for cloudlet at
[Wiki-Cloudlet](https://en.wikipedia.org/wiki/Cloudlet)

Copyright (C) 2011-2016 Carnegie Mellon University



Installing
----------

You will need:

* python-invoke

To install,

  > $ sudo apt-get install python-pip && sudo pip install invoke
  > $ git clone https://github.com/cmusatyalab/elijah-install
  > $ cd elijah-install
  > $ invoke install   % No sudo


After the successful installation, we will see the following message.

  > ..
  > ------------------------------------------------------
  > Congradulations! OpenStack++ is successfully installed.
  > 
  > Login to OpenStack Dashboard at http://localhost/
  > Here's your account information (See more at ./devstack/local.conf):
  > ID: admin
  > password: your_password_here
  > 
  > Remember to use ./restart.sh script to restart OpenStack or after the system reboot
  > $

Then, you can open Web browser and login to the OpenStack at
http://ip_address_of_the_machine/. Please read
[this](https://github.com/cmusatyalab/elijah-openstack#how-to-use) for the
detailed usage.


Please remember that you should restart openstack using after the system reboot.

  > $ cd elijah-install
  > $ ./restart.sh



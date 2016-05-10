# EON: Long timescale dynamics (for Openstack)
This software package is a fork of EON modified for usage with Openstack. The original software can be found at : http://theory.cm.utexas.edu/eon/

##Getting started

###Step 1 :
  Login to your Openstack Horizon Dashboard.
  Select your current project and region.
  Navigate to Compute -> Access & Security -> API Access
  Download the RC-file and put it in your working folder

  (For multiple cloud setup repeat Step one for each cloud)

###Step 2:
  Configure your communicator in config.ini

  Example:
  [Communicator]
  type=openstack
  openstack_rc_files=path/to/rc-file.sh;/path/to/rc-file2.sh
  openstack_n_workers=2;3

  (For multiple clients seperate with input with ";", as shown above . Enter workers in the respective order of the rc-files. )
###Step 3:
  Setup up your environment.
  Run your job, and follow initial setup for your cloud environment
  If no image for openstackeon is present choose a blank ubuntu 14.04 LTS image and select build image.

###Step 4:
  Cleaning up
  -TODO

# Housekeeping
This script can be scheduled as a cron job and will delete files and directories older than a specified amount of time.

## Usage instructions
1. Create a new config file based on the provided `config_template.cfg`
```
cp /path_to_script_dir/config_template.cfg /path_to_script_dir/my_housekeeping_job.cfg
```
1. Create a cronjob to run the script periodically
```
sudo crontab -e

# --- File contents below

# m h  dom mon dow   command
0 6 * * * /path_to_script_dir/housekeeping.sh /path_to_script_dir/my_housekeeping_job.cfg

```
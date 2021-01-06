yhosts = """sbx-iosxr-mgmt:
  hostname: sbx-iosxr-mgmt.cisco.com
  username: admin
  password: C1sco12345
  port: 8181
  platform: iosxr
  groups: 
    - slower

ios-xe-mgmt.cisco.com:
  hostname: ios-xe-mgmt.cisco.com
  username: developer
  password: C1sco12345
  port: 8181
  platform: cisco_ios
  groups: 
    - slower

ios-xe-mgmt-latest.cisco.com:
  hostname: ios-xe-mgmt-latest.cisco.com
  username: developer
  password: C1sco12345
  port: 22
  platform: cisco_ios
  groups: 
    - slow
"""

ygroups = """slower:
  connection_options:
    netmiko:
      extras:
        global_delay_factor: 3
        conn_timeout: 20

slow:
  connection_options:
    netmiko:
      extras:
        global_delay_factor: 2
"""

ydefaults = """
"""
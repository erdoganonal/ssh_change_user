This module connects to target over ssh via using paramiko module.

This module does not anything more than paramiko does.
Only allows you to send user input(such as the password) easily.

The main idea for writing that module is changing user.

Example usages:
```
    ssh = CustomSSH(host, username, password)
    ssh.change_user(target_username, target_password)

    result = ssh.exec_command('some_command')
```
Most Common Attributes:
```
    __init__:
        hostname: hostname or IP address
        username: username to connect as
        password: password for the user

    change_user:
        username: username for change to the user
        password: password for the user

    exec_command:
        command:                The command to be executed on the user
        strip_result:           A boolean value to adjust result.
                                    Trims the stripted result by index.
        join_on:                Joins the result list on given the string.
                                    Only available strip_result is set as True
        exit_on_error:          If set as True, exits when the command
                                the exit code different from 0.
        print_simultaneously:   Prints the result as soon as received.   
        

        -index:                 In some cases(like command length long),
                                    the result will be gotten wrong.
                                In such cases, the index parameter
                                    might be set as 2. The default value is 1.
        -exit_code:             Do not retrieve exit_code if you need to
                                send an input. If single input is needed,
                                `exec_command_with_input` function instead
                                migth be used instead.
        -recevice_buffer:       The maximum amount of data to be received
                                    at once.

```                     
More Examples:
```
ssh = CustomSSH(host, username, password)
ssh.change_user(target_username, target_password)

result = ssh.exec_command('some_command')
print(ssh.exit_code) # Prints the exit of the last executed command
```
```
ssh = CustomSSH(host, username, password)
ssh.change_user(target_username, target_password)

result = ssh.exec_command('some_command', exit_on_error=True) # Raises CommandReturnedNonZeroExitStatus exception
                                                              # when the exit code different from 0.
```
```
ssh = CustomSSH(host, username, password)
ssh.change_user(target_username, target_password)

result = ssh.exec_command('echo -e "\\nCustom\\nSSH\\nTest\\nCommand\\n"')
print(result) # Output is: ['', 'Custom', 'SSH', 'Test', 'Command', '']
```

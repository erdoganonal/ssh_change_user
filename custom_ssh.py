"""
Istanbul - Turkey - 2018

Author :   Erdogan Onal
Date :     2018.12.11
"""

import time as _time
import re as _re
import paramiko as _paramiko


__all__ = [
    'CustomSSHErrorBase',
    'CommandReturnedNonZeroExitStatus',
    'AuthenticationError',
    'CustomSSH'
]

__author__ = "Erdogan Onal"
__date__ = "2018.12.11"


class CustomSSHErrorBase(Exception):
    """Base Exception for CustomSSH"""


class CommandReturnedNonZeroExitStatus(CustomSSHErrorBase):
    """Exception raised when command exit code different than 0(success)

    Attributes:
        command:    The command which was run
        exit_code:  The exit code of the command
        result:     The result of the command
    """

    def __init__(self, **kwargs):
        super().__init__(
            "Command '{command}' return with"
            " error (code {exit_code}): {result}"
            "".format(**kwargs)
        )


class AuthenticationError(CustomSSHErrorBase):
    """Exception raised when authentication failed"""


class CustomSSH():
    """
        This module connects to target over ssh via using paramiko module.

        This module does not anything more than paramiko does.
        Only allows you to send user input(such as the password)
        easily.

        The main idea for writing that module is changing user.

        Example usages:
            ssh = CustomSSH(host, username, password)
            ssh.change_user(target_username, target_password)

            result = ssh.exec_command('some_command')
            exit_code = ssh.exit_code

        Example usages:
            ssh = CustomSSH(host, username, password)
            ssh.change_user(target_username, target_password)

            result = ssh.exec_command(
                'ls /non/exitsing/file',
                exit_on_error=True
            ) # Raises CommandReturnedNonZeroExitStatus error


        Most Common Attributes:
            customSSH:
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
                join_on:                Joins the result list on given the
                                            string. Only available strip_result
                                            is set as True
                exit_on_error:          If set as True, exits when the command
                                        the exit code different from 0.
                print_simultaneously:   Prints the result as soon as received.

                -index:                 In some cases(like command length long)
                                            the result will be gotten wrong.
                                            For that cases, the index parameter
                                            might be set as 2.
                                            The default value is 1.
                -exit_code:             Do not retrieve exit_code
                                            if you need to send an
                                            input. If single input is needed,
                                            `exec_command_with_input` function
                                            instead migth be used instead.
                -recevice_buffer:       The maximum amount of data
                                            to be received at once.
    """

    def __init__(self, hostname, username, password, *args, **kwargs):
        terminal = kwargs.pop('terminal', 'xterm -cm')

        self._ssh = _paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(_paramiko.AutoAddPolicy())

        self._ssh.connect(
            hostname=hostname,
            username=username,
            password=password,
            *args, **kwargs
        )

        self._shell = self._ssh.invoke_shell(term=terminal)
        self.__exit_code = '0'

        # Empty buffer
        self.exec_command("echo")

    def change_user(self, username, password, test_time=2, **kwargs):
        """
        Changes the user with given username and password.
        Also validate if operation success or not
        """
        self.exec_command_with_input(
            command='su - {0}'.format(username),
            send=password,
            control_on=('whoami', username),
            exception=AuthenticationError,
            exception_formatter=lambda result: "Username or password wrong.",
            test_time=test_time,
            **kwargs
        )

        self.__exit_code = '0'

    def open_sftp(self):
        """Opens the sftp connection"""
        return self._ssh.open_sftp()

    def exec_command_with_input(
            self,
            command, send,
            control_on=(None, None),
            receive_buffer=1024,
            **kwargs):
        """
        Executes command on the environment. In this case
        there is no exit code support.
        """

        exception = kwargs.pop('exception', Exception)
        exception_formatter = kwargs.pop(
            'exception_formatter',
            lambda result: result
        )
        test_time = kwargs.pop('test_time', 1)

        test_time = int(test_time)

        while test_time:
            test_time -= 1

            # Send command over shh
            self.exec_command(
                command,
                exit_code=False,
                receive_buffer=receive_buffer
            )
            # Wait a while
            _time.sleep(0.5)

            # Send expected command
            result = self.exec_command(
                send,
                join_on='',
                exit_code=False,
                receive_buffer=receive_buffer
            )

            if all(item is not None for item in control_on):
                result = self.exec_command(
                    control_on[0],
                    exit_code=False,
                    join_on=''
                )

                if control_on[1] != result:
                    if test_time == 0:
                        # If max time exceeded, raise
                        raise exception(exception_formatter(result))

                    # Try again
                    continue
            # break the loop
            break

    @property
    def exit_code(self):
        """
        Returns the last commands exit code
        """
        return int(self.__exit_code)

    @staticmethod
    def _get_rid_of_colors(text):
        # Regex explanation:
        # Below regex does below operation respectively
        # Finds \x1B
        # Finds ] or )
        # Finds 0-? a single character in the range between 0
        #   (index 48) and ? (index 63) [zero or unlimited]
        # Finds white space, dash or backslash [zero or unlimited]
        # Finds at, dash or tilde
        ansi_escape = _re.compile(r'\x1B[\(\[][0-?]*[ -/]*[@-~]')

        return ansi_escape.sub('', text)

    @staticmethod
    def _adjust_result(result, strip_result, join_on, index=1):
        # TODO: Find index parameter automatically.
        result = result[index:-1] if strip_result else result

        return result if join_on is None else join_on.join(result)

    def _get_exit_code(self):
        """
            Returns True if exit code 0(means success in linux),
            otherwise False.
        """

        self.__exit_code = self.exec_command(
            'echo ${?}',
            exit_code=False,
            join_on='',
            receive_buffer=1024
        )

        try:
            return int(self.__exit_code) == 0
        except ValueError:
            return False

    def exec_command(self, command,
                     join_on=None,
                     exit_on_error=False,
                     print_simultaneously=False,
                     **kwargs):
        """
        Executes the command over ssh and returns the output
        """

        # exit_code is an internal parameter, it is needed to set as False
        # if the command is needed user input.
        exit_code = kwargs.pop('exit_code', True)
        receive_buffer = kwargs.pop('receive_buffer', 9999)
        strip_result = kwargs.pop('strip_result', True)

        if kwargs:
            # We expect all kwargs are poped. If there is any
            # raise an exception
            raise TypeError(
                "Unexpected keyword argument/s: {0}"
                .format(kwargs.keys())
            )

        self.__exit_code = None

        prompt = _re.compile(r"[>\$#] *$", _re.MULTILINE)

        while True:
            self._shell.send('{0}\n'.format(command))
            _time.sleep(0.2)

            while not (self._shell.recv_ready() or self._shell.closed):
                _time.sleep(0.2)

            if exit_code:
                result = ""
                while not prompt.search(result):
                    response = self._shell.recv(receive_buffer).decode()
                    if print_simultaneously:
                        print(response)
                    result += response
            else:
                result = self._shell.recv(receive_buffer).decode()

            # Get rid of coloring
            result = self._get_rid_of_colors(result).splitlines()

            if exit_code:
                code_succeded = self._get_exit_code()

                if exit_on_error and not code_succeded:
                    raise CommandReturnedNonZeroExitStatus(
                        command=command,
                        result=self._adjust_result(
                            result, True, join_on=''),
                        exit_code=self.__exit_code
                    )

            result_length = len(result)
            result = self._adjust_result(
                result,
                strip_result=strip_result,
                join_on=join_on,
                index=kwargs.pop('index', 1)
            )

            if result_length != 1:
                return '' if result_length == 2 else result

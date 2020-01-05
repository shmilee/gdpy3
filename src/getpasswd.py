# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Class GetPasswd for both CLI and GUI of gdpy3.
'''


class GetPasswd(object):
    '''
    Set *CALLBACK* function for GUI.
    '''
    CALLBACK = None

    @classmethod
    def getpasswd(cls, prompt='Password: '):
        if cls.CALLBACK:
            return cls.CALLBACK(prompt)
        else:
            import getpass
            return getpass.getpass(prompt)

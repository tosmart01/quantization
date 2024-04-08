# -*- coding = utf-8 -*-
# @Time: 2024-04-04 21:29:19
# @Author: Donvink wuwukai
# @Site: 
# @File: base.py
# @Software: PyCharm

class BaseException(Exception):
    default_error_message = "An error occurred"
    default_error_code = 0

    def __init__(self, error_message=None, error_code=None, add_error_message=None):
        self.error_message = error_message or self.default_error_message
        self.error_code = error_code or self.default_error_code
        self.add_error_message = add_error_message
        super(BaseException, self).__init__(self.error_message, self.error_code)

    def __str__(self):
        if self.add_error_message:
            return f"{self.error_message%self.add_error_message}, error_code is:{self.error_code}"
        return f"{self.error_message}, error_code is:{self.error_code}"

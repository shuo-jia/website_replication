from captcha.fields import CaptchaField
from django.contrib.auth.forms import UserCreationForm


class RegisterUserForm(UserCreationForm):
    captcha = CaptchaField(
        label='验证码',
        required=True,
        error_messages={
            'required': '验证码不能为空'
        }
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "用户名"
        self.fields["password1"].label = "密码"
        self.fields["password2"].label = "重复密码"

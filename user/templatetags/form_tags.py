from django import template
register = template.Library()


@register.filter(name="addClass")
def addClass(field, class_str):
    """为表单字段的输入框添加 class 属性，class_str 应为类名.
    """
    return field.as_widget(attrs={"class": class_str})

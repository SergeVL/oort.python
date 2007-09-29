from paste.script import templates

class OortAppTemplate(templates.Template):
    summary = "A clean Oort web app package"
    _template_dir = 'paste_templates/oort_app'
    required_templates = ['basic_package']
    use_cheetah = False


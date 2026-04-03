from datetime import datetime

import markdown
from jinja2 import Template


def generate_html_email(markdown_content):
    # 1. Konwertuj Markdown z Gemini na HTML
    html_body = markdown.markdown(markdown_content)

    # 2. Wczytaj szablon Jinja2
    with open("email_template.html", "r", encoding="utf-8") as f:
        template_str = f.read()

    template = Template(template_str)

    # 3. Wyrenderuj finalny plik
    final_email = template.render(
        date=datetime.now().strftime("%d.%m.%p"), report_body=html_body
    )

    return final_email


# Przykład użycia:
# ai_output = "### Giełda NY\nCena wzrosła o **2.5%** z powodu suszy..."
# email_html = generate_html_email(ai_output)

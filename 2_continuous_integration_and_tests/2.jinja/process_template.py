# Processa o arquivo de configuração no arquivo de template do jinja.
import jinja2
import yaml
import os


def renderiza_template():
    # Carrega como string na variável
    with open('redshift.yaml.j2', 'r') as f:
        redshift_yaml = f.read()

    # Carrega como dicionário na variável
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Passo com base em qual arquivo quero fazer o template (em cima do arquivo lido).
    # Passa também o arq de conf e variavel de ambiene
    redshift_template = jinja2.Template(redshift_yaml)
    redshift_rendered = redshift_template.render({**config, **os.environ})
    
    # Depois encontra o arquivo e escreve nele o resultado da renderização.
    with open('redshift.yaml', 'w') as f:
        f.write(redshift_rendered)

# renderiza_template() # Ao executar, gerará o arquivo redshift.yaml.
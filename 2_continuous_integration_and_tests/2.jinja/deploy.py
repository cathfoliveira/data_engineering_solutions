import boto3
import logging
from botocore.exceptions import ClientError
import jinja2
import yaml
import os

 # Criou um client pro cloudformation
logging.getLogger().setLevel(logging.INFO)
cloudformation_client = boto3.client('cloudformation')

# Procurar "boto3 cloudformation" no google e encontramos a documentação
def create_stack(stack_name, template_body, **kwargs):
    cloudformation_client.create_stack(
        StackName=stack_name,
        TemplateBody=template_body,
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'], # Autoriza o IAM a criar os recursos com o nome que quiser
        TimeoutInMinutes=30,    # Depois de 30 min, falha e se falhar, faz um rollback.
        OnFailure='ROLLBACK'
    )
    # Retorna um objeto que espera por algo. Neste caso, aguarda a criação do stack e a cada 5 minutos quero que tente, por no máximo 600 vezes
    cloudformation_client.get_waiter('stack_create_complete').wait(
        StackName=stack_name,
        WaiterConfig={'Delay': 5, 'MaxAttempts': 600}
    )
    # Terminou o create_complete, quero mais uma confirmação pra saber se foi completo.  Se o stack existir, eureka, mas se falhar, ele vai mostrar um erro. 
    cloudformation_client.get_waiter('stack_exists').wait(StackName=stack_name)
    logging.info(f'CREATE COMPLETE')

def update_stack(stack_name, template_body, **kwargs):
    try:
        cloudformation_client.update_stack(
            StackName=stack_name,
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            TemplateBody=template_body
        )

    except ClientError as e:
        if 'No updates are to be performed' in str(e):
            logging.info(f'SKIPPING UPDATE: No updates to be performed at stack {stack_name}')
            return e

    cloudformation_client.get_waiter('stack_update_complete').wait(
        StackName=stack_name,
        WaiterConfig={'Delay': 5, 'MaxAttempts': 600}
    )

    cloudformation_client.get_waiter('stack_exists').wait(StackName=stack_name)
    logging.info(f'UPDATE COMPLETE')

# Pega os stacks com os status definidos e retorna uma lista com os nomes dos stacks.
def get_existing_stacks():
    response = cloudformation_client.list_stacks(
        StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']
    )

    return [stack['StackName'] for stack in response['StackSummaries']]


def _get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)

# Função que cria ou upd stack. Passo o arquivo como nome, ele irá abrir e ler o arquivo como string.
def create_or_update_stack():
    stack_name = f'redshift-{os.environ["ENVIRONMENT"]}'
    with open(_get_abs_path('redshift.yaml')) as f:
        template_body = f.read()

    existing_stacks = get_existing_stacks()

    if stack_name in existing_stacks:
        logging.info(f'UPDATING STACK {stack_name}')
        update_stack(stack_name, template_body)
    else:
        logging.info(f'CREATING STACK {stack_name}')
        create_stack(stack_name, template_body)


# Trouxe do process_template.py para automatizar via o deploy, ele vai renderizar internamente no github.
def renderiza_template():
    logging.info(f'RENDERING JINJA')

    # Carrega como string na variável
    with open(_get_abs_path('redshift.yaml.j2'), 'r') as f:
        redshift_yaml = f.read()

    # Carrega como dicionário na variável
    with open(_get_abs_path('config.yaml'), 'r') as f:
        config = yaml.safe_load(f)

    # Passo com base em qual arquivo quero fazer o template (em cima do arquivo lido).
    # Passa também o arq de conf e variavel de ambiene
    redshift_template = jinja2.Template(redshift_yaml)
    redshift_rendered = redshift_template.render({**config, **os.environ})
    
    # Depois encontra o arquivo e escreve nele o resultado da renderização.
    with open(_get_abs_path('redshift.yaml'), 'w') as f:
        f.write(redshift_rendered)
    logging.info(f'JINJA RENDERED')


if __name__ == '__main__':
    renderiza_template()
    create_or_update_stack()

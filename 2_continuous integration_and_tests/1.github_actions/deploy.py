import boto3
import logging
from botocore.exceptions import ClientError
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

    # Retorna um objeto que espera por algo. Neste caso, aguarda a criação do stack e a cada 5 minutos 
    # quero que tente, por no máximo 600 vezes
    cloudformation_client.get_waiter('stack_create_complete').wait(
        StackName=stack_name,
        WaiterConfig={'Delay': 5, 'MaxAttempts': 600}
    )

    # Terminou o create_complete, quero mais uma confirmação pra saber se foi completo.  Se o stack existir,
    # eureka, mas se falhar, ele vai mostrar um erro. 
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
    stack_name = 's3-bucket-ci'
    with open(_get_abs_path('bucket_github_actions.yaml')) as f:
        template_body = f.read()

    # pega as stacks existentes, se existir, faz update, senão, faz um create.
    existing_stacks = get_existing_stacks()

    if stack_name in existing_stacks:
        logging.info(f'UPDATING STACK {stack_name}')
        update_stack(stack_name, template_body)
    else:
        logging.info(f'CREATING STACK {stack_name}')
        create_stack(stack_name, template_body)


if __name__ == '__main__':
    create_or_update_stack()

# É preciso criar uma pasta "".github" na raiz do projeto para o github buscar as configs
# e as actions nela para executar o deploy. É mandatório. E dentro, criar uma pasta chamada workflows.
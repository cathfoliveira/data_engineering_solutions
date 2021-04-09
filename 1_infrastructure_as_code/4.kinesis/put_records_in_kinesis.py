
import boto3    # package python para interagir com recursos da AWS
import json
from fake_web_events import Simulation

# psycopg3: para importar os eventos para o banco de dados postgres/RDS. Neste caso, trato os eventos direto
# no código python. Para o exemplo atual trabalhado, estou colocando arquivo zipado dentro do S3.

client = boto3.client('firehose')

# Função para colocar o registro dentro do firehose
# Como o kinesis junta tudo num arquivo, uso a quebra de linha abaixo para diferenciar os eventos.
def put_record(event):
    data = json.dumps(event) + "\n"     # Converte o dicionário para uma string com a função json.dumps e quebra a linha
    response = client.put_record(
        DeliveryStreamName='kinesis-firehose-belisco',
        Record={"Data": data}
    )
    print(event)
    return response


simulation = Simulation(user_pool_size=100, sessions_per_day=10000)
events = simulation.run(duration_seconds=300)

for event in events:
    put_record(event) # Pega o evento que é um dicionário
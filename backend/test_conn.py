from elasticsearch import Elasticsearch, __version__ as es_version
from elasticsearch.exceptions import ConnectionError as ESConnectionError

print(f"Versió de la llibreria 'elasticsearch-py' instal·lada: {es_version}")
print("Provant la connexió amb Elasticsearch...")

try:
    # Fem servir 127.0.0.1 per ser més directes
    # Afegim 'verify_certs=False' per relaxar la seguretat
    es = Elasticsearch(
        hosts=["http://127.0.0.1:9200"],
        verify_certs=False
    )

    if es.ping():
        print("\n" + "="*30)
        print("  ÈXIT! La connexió de Python a Elasticsearch funciona!")
        print("="*30)
    else:
        print("\nERROR: La connexió ha funcionat però el 'ping' ha fallat.")
        print("Això pot ser un desajust de versió o configuració.")

except ESConnectionError as e:
    print("\n" + "!"*30)
    print("  HA FALLAT LA CONNEXIÓ DE PYTHON:")
    print(f"  Detall de l'error: {e}")
    print("!"*30)
except Exception as e:
    print(f"Un altre error: {e}")
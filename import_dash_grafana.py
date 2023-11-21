import os
import requests
import json
import logging
import re
import getpass
import time

print("*******************************************************")
print("*                                                     *")
print("*                    NETFLOW_FLOWBIX                  *")
print("*                                                     *")
print("*                                                     *")
print("*******************************************************")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


grafana_ip = input("Digite o IP do Grafana : ")


GRAFANA_URL = f"http://{grafana_ip}:3000/api/dashboards/db"


API_KEY = getpass.getpass("Digite a Chave Key - Token: ")


org_id_or_name = input("Digite ID da organização: ")


ORG_API_URL = f"http://{grafana_ip}:3000/api/orgs/{org_id_or_name}"


folder_path = "/home/scripts/netflow/import_dash_grafana/dashboards/"

elasticsearch_uid = input("Digite o novo UID para a fonte de dados Elasticsearch: ")


headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

try:
    org_info_response = requests.get(ORG_API_URL, headers=headers, verify=False)
    
    if org_info_response.status_code == 200:
        org_info = org_info_response.json()

        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(folder_path, filename)

                try:
                    with open(file_path, "r+") as file:
                        panel_data = json.load(file)

                        for panel in panel_data.get("panels", []):
                            datasource = panel.get("datasource", {})
                            if datasource and datasource.get("type") == "elasticsearch":
                                datasource["uid"] = elasticsearch_uid

                            targets = panel.get("targets", [])
                            for target in targets:
                                target_datasource = target.get("datasource", {})
                                if target_datasource and target_datasource.get("type") == "elasticsearch":
                                    target_datasource["uid"] = elasticsearch_uid

                            # Check and update UID inside "templating"
                            templating = panel_data.get("templating", {})
                            if templating:
                                for option in templating.get("list", []):
                                    datasource = option.get("datasource", {})
                                    if datasource and datasource.get("type") == "elasticsearch":
                                        datasource["uid"] = elasticsearch_uid

                        file.seek(0)
                        json.dump(panel_data, file, indent=4)
                        file.truncate()

                        dashboard_name = re.sub(r'-\d+$', '', os.path.splitext(filename)[0])

                        dashboard_data = {
                            "dashboard": {
                                "id": None,
                                "uid": panel_data.get("uid"),
                                "title": dashboard_name,
                                "panels": panel_data["panels"],
                                "templating": panel_data.get("templating")
                            },
                            "message": f"Importado a partir do arquivo '{filename}'",
                            "overwrite": False
                        }

                        response = requests.post(GRAFANA_URL, headers=headers, json=dashboard_data, verify=False)

                        if response.status_code == 200:
                            logger.info(f"Painel do arquivo '{filename}' importado com sucesso para '{dashboard_name}' na organização '{org_info['name']}'!")
                        else:
                            logger.error(f"Falha ao importar o painel do arquivo '{filename}'. Código de status: {response.status_code}")
                            logger.error(response.text)
                        time.sleep(1)
                except Exception as e:
                    logger.error(f"Erro ao processar o arquivo '{filename}': {str(e)}")
    else:
        logger.error(f"Organização '{org_id_or_name}' não encontrada. Código de status: {org_info_response.status_code}")
except Exception as e:
    logger.error(f"Erro ao obter informações da organização: {str(e)}")